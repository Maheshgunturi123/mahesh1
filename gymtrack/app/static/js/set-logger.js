// Set logger stub — will be expanded in future stories
(function() {
    'use strict';
    window.GymTrack = window.GymTrack || {};
    window.GymTrack.logger = {
        log: function(msg) { console.log('[GymTrack]', msg); },
        error: function(msg) { console.error('[GymTrack]', msg); }
    };
})();
