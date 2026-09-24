# BACKLOG-jaswarm.md - heros-v3 (committed)

Real issues flagged but not fixed, with what + where + why deferred.

- [ ] 2026-09-24 services/index.html thumbnails (yard debris, appliance, sofa, estate) read as stock to both judges on all three builds; needs the client's real job photos (Jack). Also on rebuild/v3b and rebuild/v3c.

- [ ] 2026-09-24 assets/house-scene.js: while the piece flies to the nav (scrollY ~150-775 at 1440) the reparented canvas grows to ~500px and paints above the header top edge (stray accent block). Needs a runtime change (clamp the transitional rect to the nav box); CSS cannot reach a body-level fixed canvas.

- [ ] 2026-09-24 round 2 SEO pass, 10 meta descriptions still run 161-176 chars (construction-debris 170, estate-cleanouts 172, services/index 161, junk-removal-little-elm 168, junk-removal-mckinney 176, junk-removal-plano 170, junk-removal-prosper 166, same-day-junk-removal 171, yard-debris 163, areas.html 161). Left un-shortened on purpose: every remaining sentence is either a specific service/city fact list or explicit area wording (city names, "7 days a week" area claims), and this round's brief carries a hard exclusion on touching service-area wording. A further trim needs either cutting a real fact (risk) or Jack's sign-off to touch area phrasing once the real service area is confirmed.
