# BACKLOG-jaswarm.md - heros-v3 (committed)

Real issues flagged but not fixed, with what + where + why deferred.

- [ ] 2026-09-24 services/index.html thumbnails (yard debris, appliance, sofa, estate) read as stock to both judges on all three builds; needs the client's real job photos (Jack). Also on rebuild/v3b and rebuild/v3c.

- [ ] 2026-09-24 assets/house-scene.js: while the piece flies to the nav (scrollY ~150-775 at 1440) the reparented canvas grows to ~500px and paints above the header top edge (stray accent block). Needs a runtime change (clamp the transitional rect to the nav box); CSS cannot reach a body-level fixed canvas.
