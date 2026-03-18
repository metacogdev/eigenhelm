//go:build linux

package robustness

import (
	"bytes"
	"crypto/rand"
	"fmt"
	"io"
	"math"
	"math/big"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"go.etcd.io/bbolt/tests/dmflakey"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"golang.org/x/sys/unix"
)

var panicFailpoints = []string{
	"beforeSyncDataPages",
	"beforeSyncMetaPage",
	"lackOfDiskSpace",
	"mapError",
	"resizeFileError",
	"unmapError",
}

// TestRestartFromPowerFailureExt4 is to test data after unexpected power failure on ext4.
func TestRestartFromPowerFailureExt4(t *testing.T) {
	for _, tc := range []struct {
		name         string
		du           time.Duration
		fsMountOpt   string
		useFailpoint bool
	}{
		{
			name:         "fp_ext4_commit5s",
			du:           5 * time.Second,
			fsMountOpt:   "commit=5",
			useFailpoint: true,
		},
		{
			name:         "fp_ext4_commit1s",
			du:           10 * time.Second,
			fsMountOpt:   "commit=1",
			useFailpoint: true,
		},
		{
			name:         "fp_ext4_commit1000s",
			du:           10 * time.Second,
			fsMountOpt:   "commit=1000",
			useFailpoint: true,
		},
		{
			name:       "kill_ext4_commit5s",
			du:         5 * time.Second,
			fsMountOpt: "commit=5",
		},
		{
			name:       "kill_ext4_commit1s",
			du:         10 * time.Second,
			fsMountOpt: "commit=1",
		},
		{
			name:       "kill_ext4_commit1000s",
			du:         10 * time.Second,
			fsMountOpt: "commit=1000",
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			doPowerFailure(t, tc.du, dmflakey.FSTypeEXT4, "", tc.fsMountOpt, tc.useFailpoint)
		})
	}
}

func TestRestartFromPowerFailureXFS(t *testing.T) {
	for _, tc := range []struct {
		name         string
		mkfsOpt      string
		fsMountOpt   string
		useFailpoint bool
	}{
		{
			name:         "xfs_no_opts",
			mkfsOpt:      "",
			fsMountOpt:   "",
			useFailpoint: true,
		},
		{
			name:         "lazy-log",
			mkfsOpt:      "-l lazy-count=1",
			fsMountOpt:   "",
			useFailpoint: true,
		},
		{
			name:         "odd-allocsize",
			mkfsOpt:      "",
			fsMountOpt:   "allocsize=" + fmt.Sprintf("%d", 4096*5),
			useFailpoint: true,
		},
		{
			name:         "nolargeio",
			mkfsOpt:      "",
			fsMountOpt:   "nolargeio",
			useFailpoint: true,
		},
		{
			name:         "odd-alignment",
			mkfsOpt:      "-d sunit=1024,swidth=1024",
			fsMountOpt:   "noalign",
			useFailpoint: true,
		},
		{
			name:    "openshift-sno-options",
			mkfsOpt: "-m bigtime=1,finobt=1,rmapbt=0,reflink=1 -i sparse=1 -l lazy-count=1",
			// openshift also supplies seclabel,relatime,prjquota on RHEL, but that's not supported on our CI
			// prjquota is only unsupported on our ARM runners.
			// You can find more information in either the man page with `man xfs` or `man mkfs.xfs`.
			// Also refer to https://man7.org/linux/man-pages/man8/mkfs.xfs.8.html.
			fsMountOpt:   "rw,attr2,inode64,logbufs=8,logbsize=32k",
			useFailpoint: true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			t.Logf("mkfs opts: %s", tc.mkfsOpt)
			t.Logf("mount opts: %s", tc.fsMountOpt)
			doPowerFailure(t, 5*time.Second, dmflakey.FSTypeXFS, tc.mkfsOpt, tc.fsMountOpt, tc.useFailpoint)
		})
	}
}

func doPowerFailure(t *testing.T, du time.Duration, fsType dmflakey.FSType, mkfsOpt string, fsMountOpt string, useFailpoint bool) {
	flakey := initFlakeyDevice(t, strings.Replace(t.Name(), "/", "_", -1), fsType, mkfsOpt, fsMountOpt)
	root := flakey.RootFS()

	dbPath := filepath.Join(root, "boltdb")

	args := []string{"bbolt", "bench",
		"-work", // keep the database
		"-path", dbPath,
		"-count=1000000000",
		"-batch-size=5", // separate total count into multiple truncation
		"-value-size=512",
	}

	logPath := filepath.Join(t.TempDir(), fmt.Sprintf("%s.log", t.Name()))
	require.NoError(t, os.MkdirAll(path.Dir(logPath), 0600))

	logFd, err := os.Create(logPath)
	require.NoError(t, err)
	defer logFd.Close()

	fpURL := "127.0.0.1:12345"

	cmd := exec.Command(args[0], args[1:]...)
	cmd.Stdout = logFd
	cmd.Stderr = logFd
	cmd.Env = append(cmd.Env, "GOFAIL_HTTP="+fpURL)
	t.Logf("start %s", strings.Join(args, " "))
	require.NoError(t, cmd.Start(), "args: %v", args)

	errCh := make(chan error, 1)
	go func() {
		errCh <- cmd.Wait()
	}()

	defer func() {
		if t.Failed() {
			logData, err := os.ReadFile(logPath)
			assert.NoError(t, err)
			t.Logf("dump log:\n: %s", string(logData))
		}
	}()

	time.Sleep(du)
	t.Logf("simulate power failure")

	if useFailpoint {
		fpURL = "http://" + fpURL
		targetFp := panicFailpoints[randomInt(t, math.MaxInt32)%len(panicFailpoints)]
		t.Logf("random pick failpoint: %s", targetFp)
		activeFailpoint(t, fpURL, targetFp, "panic")
	} else {
		t.Log("kill bbolt")
		assert.NoError(t, cmd.Process.Kill())
	}

	select {
	case <-time.After(10 * time.Second):
		t.Log("bbolt is supposed to be already stopped, but actually not yet; forcibly kill it")
