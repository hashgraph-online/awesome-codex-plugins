// Node entry for the character kit: loads every module into one B2M object. In a page, load the same files
// with <script> tags in this order: poses.js, rig.js, shapes.js, render.js, skins.js, skins-extra.js, stage.js.
'use strict';
require('./poses.js');
require('./rig.js');
require('./shapes.js');
require('./render.js');
require('./skins.js');
require('./skins-extra.js');
require('./stage.js');
module.exports = globalThis.B2M;
