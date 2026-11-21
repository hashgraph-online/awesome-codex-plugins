import { runDelivery } from '../src/core/delivery.mjs'
runDelivery(process.argv[2]).catch(error => { console.error(error.message); process.exit(1) })
