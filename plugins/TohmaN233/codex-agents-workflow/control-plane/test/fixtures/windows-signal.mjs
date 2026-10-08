// Windows child.kill(SIGTERM) forcibly terminates Node, bypassing JS handlers.
// Exercise the actual production signal listener in a separate process via IPC.
process.on('message', message => { if (message === 'emit-sigterm') process.emit('SIGTERM'); });
