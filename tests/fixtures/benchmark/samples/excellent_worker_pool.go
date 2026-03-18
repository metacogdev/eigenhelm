package benchmark

import "sync"

type Job func()

type WorkerPool struct {
	jobs    chan Job
	wg      sync.WaitGroup
	quit    chan struct{}
	stopped bool
}

func NewWorkerPool(workers, queueSize int) *WorkerPool {
	p := &WorkerPool{
		jobs: make(chan Job, queueSize),
		quit: make(chan struct{}),
	}
	p.wg.Add(workers)
	for range workers {
		go p.worker()
	}
	return p
}

func (p *WorkerPool) worker() {
	defer p.wg.Done()
	for {
		select {
		case job, ok := <-p.jobs:
			if !ok {
				return
			}
			job()
		case <-p.quit:
			return
		}
	}
}

func (p *WorkerPool) Submit(job Job) bool {
	if p.stopped {
		return false
	}
	select {
	case p.jobs <- job:
		return true
	case <-p.quit:
		return false
	}
}

func (p *WorkerPool) Shutdown() {
	p.stopped = true
	close(p.quit)
	p.wg.Wait()
}
