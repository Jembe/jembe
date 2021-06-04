import { JembeClient } from "./client.js";
window.jembeClient = new JembeClient(document)
window.jembeClient.dispatchUpdatePageEvent(false, false)