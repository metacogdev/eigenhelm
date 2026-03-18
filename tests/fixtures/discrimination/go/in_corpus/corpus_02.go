package common

import (
	"fmt"
	"os"
	"sort"
	"unsafe"
)

const PageHeaderSize = unsafe.Sizeof(Page{})

const MinKeysPerPage = 2

const BranchPageElementSize = unsafe.Sizeof(branchPageElement{})
const LeafPageElementSize = unsafe.Sizeof(leafPageElement{})
const pgidSize = unsafe.Sizeof(Pgid(0))

const (
	BranchPageFlag   = 0x01
	LeafPageFlag     = 0x02
	MetaPageFlag     = 0x04
	FreelistPageFlag = 0x10
)

const (
	BucketLeafFlag = 0x01
)

type Pgid uint64

type Page struct {
	id       Pgid
	flags    uint16
	count    uint16
	overflow uint32
}

func NewPage(id Pgid, flags, count uint16, overflow uint32) *Page {
	return &Page{
		id:       id,
		flags:    flags,
		count:    count,
		overflow: overflow,
	}
}

// Typ returns a human-readable page type string used for debugging.
func (p *Page) Typ() string {
	if p.IsBranchPage() {
		return "branch"
	} else if p.IsLeafPage() {
		return "leaf"
	} else if p.IsMetaPage() {
		return "meta"
	} else if p.IsFreelistPage() {
		return "freelist"
	}
	return fmt.Sprintf("unknown<%02x>", p.flags)
}

func (p *Page) IsBranchPage() bool {
	return p.flags == BranchPageFlag
}

func (p *Page) IsLeafPage() bool {
	return p.flags == LeafPageFlag
}

func (p *Page) IsMetaPage() bool {
	return p.flags == MetaPageFlag
}

func (p *Page) IsFreelistPage() bool {
	return p.flags == FreelistPageFlag
}

// Meta returns a pointer to the metadata section of the page.
func (p *Page) Meta() *Meta {
	return (*Meta)(UnsafeAdd(unsafe.Pointer(p), unsafe.Sizeof(*p)))
}

func (p *Page) FastCheck(id Pgid) {
	Assert(p.id == id, "Page expected to be: %v, but self identifies as %v", id, p.id)
	// Only one flag of page-type can be set.
	Assert(p.IsBranchPage() ||
		p.IsLeafPage() ||
		p.IsMetaPage() ||
		p.IsFreelistPage(),
		"page %v: has unexpected type/flags: %x", p.id, p.flags)
}

// LeafPageElement retrieves the leaf node by index
func (p *Page) LeafPageElement(index uint16) *leafPageElement {
	return (*leafPageElement)(UnsafeIndex(unsafe.Pointer(p), unsafe.Sizeof(*p),
		LeafPageElementSize, int(index)))
}

// LeafPageElements retrieves a list of leaf nodes.
func (p *Page) LeafPageElements() []leafPageElement {
	if p.count == 0 {
		return nil
	}
	data := UnsafeAdd(unsafe.Pointer(p), unsafe.Sizeof(*p))
	elems := unsafe.Slice((*leafPageElement)(data), int(p.count))
	return elems
}

// BranchPageElement retrieves the branch node by index
func (p *Page) BranchPageElement(index uint16) *branchPageElement {
	return (*branchPageElement)(UnsafeIndex(unsafe.Pointer(p), unsafe.Sizeof(*p),
		unsafe.Sizeof(branchPageElement{}), int(index)))
}

// BranchPageElements retrieves a list of branch nodes.
func (p *Page) BranchPageElements() []branchPageElement {
	if p.count == 0 {
		return nil
	}
	data := UnsafeAdd(unsafe.Pointer(p), unsafe.Sizeof(*p))
	elems := unsafe.Slice((*branchPageElement)(data), int(p.count))
	return elems
}

func (p *Page) FreelistPageCount() (int, int) {
	Assert(p.IsFreelistPage(), fmt.Sprintf("can't get freelist page count from a non-freelist page: %2x", p.flags))

	// If the page.count is at the max uint16 value (64k) then it's considered
	// an overflow and the size of the freelist is stored as the first element.
	var idx, count = 0, int(p.count)
	if count == 0xFFFF {
		idx = 1
		c := *(*Pgid)(UnsafeAdd(unsafe.Pointer(p), unsafe.Sizeof(*p)))
		count = int(c)
		if count < 0 {
			panic(fmt.Sprintf("leading element count %d overflows int", c))
		}
	}

	return idx, count
}

func (p *Page) FreelistPageIds() []Pgid {
	Assert(p.IsFreelistPage(), fmt.Sprintf("can't get freelist page IDs from a non-freelist page: %2x", p.flags))

	idx, count := p.FreelistPageCount()

	if count == 0 {
		return nil
	}

	data := UnsafeIndex(unsafe.Pointer(p), unsafe.Sizeof(*p), pgidSize, idx)
	ids := unsafe.Slice((*Pgid)(data), count)

	return ids
}

// dump writes n bytes of the page to STDERR as hex output.
func (p *Page) hexdump(n int) {
	buf := UnsafeByteSlice(unsafe.Pointer(p), 0, 0, n)
	fmt.Fprintf(os.Stderr, "%x\n", buf)
}

func (p *Page) PageElementSize() uintptr {
	if p.IsLeafPage() {
		return LeafPageElementSize
	}
	return BranchPageElementSize
}

func (p *Page) Id() Pgid {
	return p.id
}

func (p *Page) SetId(target Pgid) {
	p.id = target
}

func (p *Page) Flags() uint16 {
	return p.flags
}

func (p *Page) SetFlags(v uint16) {
	p.flags = v
}

func (p *Page) Count() uint16 {
	return p.count
}

func (p *Page) SetCount(target uint16) {
	p.count = target
}

func (p *Page) Overflow() uint32 {
	return p.overflow
}

func (p *Page) SetOverflow(target uint32) {
	p.overflow = target
}
