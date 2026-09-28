#!/usr/bin/env python
"""Two city+service pages for each city added in round 2 (Dallas, Carrollton, The Colony, Wylie).

Each page is built on the markup of an existing city+service sibling of the same service
(same sections, reviews band, cube docks, CTAs, other-services tiles) with its own copy,
head, hero photo, FAQ and JSON-LD. The header/footer are refreshed afterwards by
scripts/trinity_chrome.py, so whatever chrome the template carries does not matter.

Usage: python scripts/new_city_services.py        (writes services/<slug>.html)
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVC = ROOT / 'services'
BASE = 'https://herosjunkremovaltx.com'

TEMPLATES = {
    'furniture': 'furniture-removal-plano.html',
    'couch': 'couch-removal-frisco.html',
    'mattress': 'mattress-removal-allen.html',
    'appliance': 'appliance-pickup-plano.html',
    'yard': 'yard-waste-removal-allen.html',
}

PHOTOS = {
    'desk': dict(ratio='1100/1467', stem='job-desk', w=820, h=1093, big='1100w',
                 alt='A black desk in a home office, ready for pickup'),
    'shelf': dict(ratio='1100/1467', stem='job-wire-shelf', w=820, h=1093, big='1100w',
                  alt='A black wire shelving unit, ready for pickup'),
    'storage': dict(ratio='956/1390', stem='job-storage-unit', w=820, h=1192, big='956w',
                    alt='A leather sectional and a wood dresser in a storage unit, ready to go'),
    'bed': dict(ratio='1100/1461', stem='job-bed-mattress', w=820, h=1089, big='1100w',
                alt='A bed frame and mattress in a bedroom, ready for pickup'),
}

TCEQ = '<a href="https://www.tceq.texas.gov/" target="_blank" rel="noopener noreferrer">TCEQ</a>'
EPA = '<a href="https://www.epa.gov/recycle/composting-home" target="_blank" rel="noopener noreferrer">EPA&#x27;s composting guide</a>'

NUMBER = ('    <h2>How you get your number</h2>\n'
          '    <p>Send photos or we come look. You get a firm number before anything is lifted, and the number holds once the work starts. No weight tickets, no hourly clock. When you are ready, <a href="../contact.html">tell us what you have</a>.</p>\n'
          '    <p>Our own people do the carrying, not gig labor hired off an app that morning. Nash owns the company and works every job himself, which is why we are comfortable sending a crew inside a house rather than only working a driveway. Usable pieces go to local donation partners, and <a href="../blog/where-your-junk-goes-after-pickup.html">where your junk actually goes</a> walks through the rest.</p>\n')

DALLAS_FAST = ('For the north side of the city, a call before noon often means the same afternoon. Further south we give you an honest window rather than a promise. '
               'Typical rather than guaranteed either way, since access and job size are real variables.')
NOT_BAGGED = 'No. The crew loads loose piles as they sit, from the backyard, side yard or curb. Bagging speeds loading up but is never required.'

PAGES = [
    # ------------------------------------------------------------------ Dallas
    dict(
        slug='furniture-removal-dallas', kind='furniture', city='Dallas', svc='Furniture Removal', photo='desk',
        desc='Furniture removal in Dallas, TX. Apartment, condo and house furniture carried out, taken apart when needed and donated when usable, 7 days a week.',
        lead_hero='A sofa out of a third-floor walk-up, a bedroom set out of a long-owned house, or a desk left behind in a home office. We carry it out and donate what still has life in it.',
        lead='Dallas is the largest city we work, and its furniture calls come from every kind of building: apartments and condos with an elevator to book, older houses where the same bedroom set has sat for decades, and home offices being cleared after a move. The job is the same in all of them. We carry it out, take it apart when the doorway calls for it, and donate what can still be used.',
        involves='Most Dallas furniture pickups start with the building rather than the furniture. In an apartment or condo, the questions are whether there is a freight elevator, whether the property wants the loading area reserved, and how far the hallway runs from the unit to the door. In a house, it is the stairs, the tight turn at the top of them, and whether a solid wood dresser or an armoire will clear the bedroom door without coming apart. The crew pads corners and door frames, takes bed frames down to rails and headboards, pulls the legs off tables, and separates sectionals at the brackets so nothing gets forced through sideways. Desks, bookcases and entertainment centers are handled the same way, and a heavy piece is carried rather than dragged across the floor.',
        different='Dallas has far more apartment buildings, condos and shared drives than the suburbs north of it, so the most useful thing you can tell us is the approach: the floor, the elevator, any loading dock rules, and whether the trailer can sit in a driveway, an alley or only on the street. The northern side of the city, closest to Carrollton, Plano and the rest of our area, is the quickest for us to reach. For addresses further south we still take the job and give you an honest window instead of promising the afternoon. If the city&#x27;s bulk collection will take a single piece on a date that works for you, use it. Where we fit is furniture that has to leave on a specific day, come down from an upper floor, or go out as a whole room at once.',
        more='the main <a href="furniture-removal.html">Furniture Removal</a> page. And for the rest of what we cover in Dallas, see <a href="junk-removal-dallas.html">junk removal in Dallas</a>, or <a href="appliance-pickup-dallas.html">appliance pickup in Dallas</a> if a fridge or washer is going too. We run the same service for <a href="furniture-removal-plano.html">furniture hauling in Plano</a> and <a href="furniture-removal-the-colony.html">furniture hauling in The Colony</a>.',
        faqs=[
            ('Can you get furniture out of a Dallas apartment with no freight elevator?', 'Yes. Tell us the floor and the stairwell when you write. Beds, sectionals and tables come apart so they carry down the stairs safely, and the price you get by text already accounts for the carry.'),
            ('Do I need to reserve the loading dock at my Dallas building?', 'If your building has one and requires a reservation, yes, and the management office is who books it. Tell us the window you get and we plan the pickup inside it.'),
            ('Will you take apart a bed frame, a desk or a sectional?', 'Yes. Bed frames, desks, bookcases and sectionals come apart as part of the pickup, not as an add-on, so they clear doors and stairwells without damage.'),
            ('Does usable furniture from a Dallas pickup get donated?', 'Yes. Clean, usable pieces go to local donation partners first. Only what cannot be donated is broken down for recycling or disposal.'),
            ('How fast can you pick up furniture in Dallas?', DALLAS_FAST),
        ]),
    dict(
        slug='appliance-pickup-dallas', kind='appliance', city='Dallas', svc='Appliance Pickup',
        desc='Appliance pickup in Dallas, TX. Fridges, washers, dryers and water heaters carried out of houses and apartments and recycled, 7 days a week.',
        lead_hero='A dead fridge in a condo kitchen, a washer and dryer left in an apartment closet, or the water heater that finally gave out. We carry it out and route it to recyclers.',
        lead='Appliances in Dallas come out of every kind of home, from a stacked washer and dryer in an apartment closet to a garage freezer that has run for twenty years. We handle the simple disconnection, carry the unit out, and send it to a recycler instead of a landfill.',
        involves='An appliance pickup is mostly about the path out. A refrigerator has to clear the kitchen opening, the hallway and the front door, and in a Dallas apartment or condo it also has to fit the elevator or go down the stairs on a dolly with straps. Stacked washer and dryer units usually separate before they move. The crew handles the basic disconnection on the spot (unplugging, water supply lines, the dryer vent); gas lines need a licensed plumber to cap them first and hardwired units need an electrician, and we take it from there once that step is done. Fridges, freezers, window units and dehumidifiers hold refrigerant, so they go to certified recyclers who recover it before the steel is reclaimed. Working units in good condition can go to donation instead.',
        different='Building rules shape more Dallas appliance pickups than anything about the appliance itself. Many apartment and condo buildings want the service elevator or the loading area reserved for anything this heavy, so check with the management office and tell us the window. For a house, tell us whether the unit is in a garage, a utility room or the kitchen, and whether the trailer can reach the driveway or an alley. The northern side of the city is the quickest for us to reach; further south we give you an honest window instead of promising the afternoon. Anything that leaked out of an old appliance, along with paint, fuel and chemicals stored near it, goes to a household chemical collection program rather than on our trailer.',
        more='the main <a href="appliance-removal.html">Appliance Removal</a> page. And for the rest of what we cover in Dallas, see <a href="junk-removal-dallas.html">junk removal in Dallas</a>, or <a href="furniture-removal-dallas.html">furniture removal in Dallas</a> if the couch is going too. We run the same crew and the same pricing model for <a href="appliance-pickup-plano.html">an old fridge or washer in Plano</a> and <a href="appliance-pickup-wylie.html">an old fridge or washer in Wylie</a>.',
        faqs=[
            ('Can you move a refrigerator out of a Dallas apartment or condo?', 'Yes. Tell us the floor, whether there is an elevator, and whether the building needs the service elevator or loading area reserved. The crew brings an appliance dolly and straps and plans the carry around it.'),
            ('Do you disconnect the washer, dryer or water heater?', 'We handle the simple part: unplugging, water supply lines and the dryer vent. Gas lines need a licensed plumber to cap them first and hardwired units need an electrician. Once that is done, we take it from there.'),
            ('What happens to the refrigerant in an old Dallas fridge?', 'Units that hold refrigerant go to certified recyclers who recover it before the metal is reclaimed, rather than to a landfill.'),
            ('Can a working appliance be donated instead of scrapped?', 'Yes. Clean, working units go to local donation partners first, and units that no longer work are routed to metal recyclers.'),
            ('How fast can you pick up an appliance in Dallas?', DALLAS_FAST),
        ]),
    # ------------------------------------------------------------------ Carrollton
    dict(
        slug='couch-removal-carrollton', kind='couch', city='Carrollton', svc='Couch Removal', photo='storage',
        desc='Couch and sofa removal in Carrollton, TX. Sectionals, sleepers and recliners carried out and donated when usable, anywhere in the city, 7 days a week.',
        lead_hero='A sectional that will not fit the next living room, a sleeper sofa nobody sleeps on, or a recliner that finally quit. We carry it out and donate what still has life in it.',
        lead='A couch is one of the most common single pieces we carry out of a house, and in Carrollton the reasons vary as much as the city does: a move out of an established house, a new sectional arriving next week, or a sofa left behind when a rental turns over. Carrollton reaches into Dallas, Denton and Collin counties, and we work all three parts of it the same way.',
        involves='Most couches come out whole, but the big ones do not have to. Sectionals separate at the connector brackets, piece by piece, so a wraparound clears a standard door without being forced through sideways. Sleeper sofas are the heaviest thing in most living rooms because of the steel fold-out frame inside, and the frame often has to come out, or the sofa has to tip on end, to clear a doorway. Power recliners have motors and wiring, so they are unplugged and carried rather than dragged. Legs come off before the lift, door frames get padded, and the crew carries the couch rather than sliding it across the floor. All of that is part of the pickup, not an add-on.',
        different='Some Carrollton neighborhoods are set up for alley collection, and an alley can put the trailer right at the back gate, which makes for a shorter carry than the front door and the driveway. It can also be tight, so tell us which side of the house is easier when you write. Carrollton sits right on our regular route, so a call before noon typically means the same afternoon. A couch set out at the curb early for a bulk collection day can sit there longer than planned, so we load and leave in one visit instead of asking you to stage it.',
        more='the main <a href="furniture-removal.html">Furniture Removal</a> page. And for the rest of what we cover in Carrollton, see <a href="junk-removal-carrollton.html">junk removal in Carrollton</a>, and if it is a mattress instead, see <a href="mattress-removal-carrollton.html">mattress removal in Carrollton</a>. The same crew also handles <a href="couch-removal-frisco.html">couch pickup in Frisco</a> and <a href="couch-removal-mckinney.html">couch pickup in McKinney</a>.',
        faqs=[
            ('Can you take a sectional apart to get it out of a Carrollton house?', 'Yes. Sectionals separate at the connector brackets and sleeper sofas come apart at the frame, and the crew handles both as part of the pickup. Mention stairs or a narrow hallway when you write.'),
            ('Is a sleeper sofa harder to remove than a regular couch?', 'It is heavier, because of the steel fold-out frame inside, but it is a normal pickup for us. The frame comes out or the sofa tips on end to clear the door, and the price you get by text already accounts for it.'),
            ('Do you donate a couch that is still in good shape?', 'Yes. Clean, intact couches go to local donation partners first. A couch that is torn, stained or damaged usually cannot be donated, and only what cannot be donated is broken down for recycling or disposal.'),
            ('Can you pick up from the alley side of a Carrollton house?', 'Yes. Some Carrollton neighborhoods are alley collection, and we work from the alley or the driveway, whichever gives the shorter, safer carry. Tell us which when you write.'),
            ('How fast can you get a couch out of a Carrollton house?', 'Carrollton sits on our regular route, so a call before noon typically means the same afternoon. Typical rather than guaranteed, since access and job size are real variables.'),
        ]),
    dict(
        slug='mattress-removal-carrollton', kind='mattress', city='Carrollton', svc='Mattress Removal', photo='bed',
        desc='Mattress removal in Carrollton, TX. Mattresses, box springs and bed frames carried out together and donated when they still qualify, 7 days a week.',
        lead_hero='The old mattress that has to be gone before the new one arrives, or a whole bedroom being cleared before a move. We carry it out, box spring and frame included.',
        lead='Most Carrollton mattress calls are about timing: a new mattress is on its way and the old one has to be out of the bedroom first, or a house is being cleared ahead of a move and the beds are the last big pieces left. We carry the mattress, box spring and frame out as one pickup.',
        involves='A mattress is awkward rather than heavy. A queen or king bends on a tight stair turn, and a thick pillow-top or a hybrid with a coil core weighs more than it looks, so the crew carries it rather than sliding it down the stairs. Box springs are rigid and go out flat. Bed frames come apart at the rails and the headboard, and adjustable bases, which have motors and wiring, are unplugged and carried as their own piece. Texas has no statewide mattress recycling program, so a mattress that cannot be donated is separated for its steel coils and foam where a processor accepts it, rather than going straight to a landfill by default.',
        different='Carrollton has a mix of established neighborhoods and newer ones, and the difference shows up in the carry rather than the mattress. A two-story house means a stairwell to plan for, and some older blocks are alley collection, which can put the trailer closer to a back door than the street. Tell us the floor and which side of the house is easier when you write. If a new mattress is being delivered, give us the delivery window and we plan the pickup so the bedroom is clear first. We load and leave the same visit rather than leaving a mattress at the curb to wait for a collection day.',
        more='the main <a href="furniture-removal.html">Furniture Removal</a> page. And for the rest of what we cover in Carrollton, see <a href="junk-removal-carrollton.html">junk removal in Carrollton</a>, and if the couch is going too, see <a href="couch-removal-carrollton.html">couch removal in Carrollton</a>. We run the same crew for <a href="mattress-removal-frisco.html">mattress pickup in Frisco</a> and <a href="mattress-removal-allen.html">mattress pickup in Allen</a>.',
        faqs=[
            ('Do you take the box spring and bed frame too?', 'Yes, as one pickup. The frame comes apart at the rails and headboard, and the box spring goes out flat with the mattress.'),
            ('Can you time a Carrollton pickup around a new mattress delivery?', 'Yes. Tell us the delivery window and we plan the old mattress&#x27;s pickup so the bedroom is clear before the new one arrives.'),
            ('Is there a mattress recycling program in Texas?', 'No statewide mattress recycling program exists in Texas. A mattress that cannot be donated is separated for recyclable steel and foam where a processor accepts it.'),
            ('Will a king mattress fit down the stairs of a two-story house?', 'Almost always. Queens and kings bend enough to clear a stair turn, and the crew carries rather than slides them so walls and banisters stay clean. Mention the stairs when you write.'),
            ('How fast can you get a mattress out of a Carrollton house?', 'Carrollton sits on our regular route, so a call before noon typically means the same afternoon. Typical rather than guaranteed, since access and job size are real variables.'),
        ]),
    # ------------------------------------------------------------------ The Colony
    dict(
        slug='furniture-removal-the-colony', kind='furniture', city='The Colony', svc='Furniture Removal', photo='shelf',
        desc='Furniture removal in The Colony, TX. Indoor furniture and weathered patio sets carried out on the east shore of Lewisville Lake, 7 days a week.',
        lead_hero='A living room set before a move, shelving and a desk out of a spare room, or patio furniture the sun has finished off. We carry it out and donate what still has life in it.',
        lead='The Colony sits on the east shore of Lewisville Lake, between Frisco and Little Elm, and its furniture calls come in two kinds: indoor pieces leaving with a move, a downsizing or a new set, and outdoor furniture that the sun and weather by the lake have worn out. We take both, from inside the house or off the back patio.',
        involves='Indoor furniture is about the route out. Dressers and bookcases get carried rather than dragged, bed frames come apart at the rails, sectionals separate at the brackets, and shelving units and desks come down to flat pieces where that makes the carry safer. The crew pads door frames and corners before anything heavy moves. Outdoor furniture is a different load: aluminum and wrought iron frames, glass tabletops, cushions that have soaked up years of rain, and umbrella bases filled with sand or concrete. Glass tops come off first and travel separately, metal frames go to recyclers, and anything too weathered to reuse goes to disposal.',
        different='Being next to the lake shapes what we carry here. Patio sets, outdoor sofas and deck furniture wear out in full sun and wind, so they are a regular part of what we haul in The Colony, and weathered outdoor pieces are usually past donating. Clean indoor pieces are the opposite, and they go to local donation partners first. Some streets near the water are tighter than the newer additions further from it, so tell us about a shared drive, a narrow street or a gate when you write and the crew plans the approach. The Colony is next door to Frisco and Little Elm, two cities we have worked since the start, so a call before noon typically means the same afternoon.',
        more='the main <a href="furniture-removal.html">Furniture Removal</a> page. And for the rest of what we cover in The Colony, see <a href="junk-removal-the-colony.html">junk removal in The Colony</a>, and if the job is out in the yard too, see <a href="yard-waste-removal-the-colony.html">yard waste removal in The Colony</a>. We run the same service for <a href="furniture-removal-plano.html">furniture hauling in Plano</a> and <a href="furniture-removal-dallas.html">furniture hauling in Dallas</a>.',
        faqs=[
            ('Do you take old patio furniture, not just indoor pieces?', 'Yes. Patio sets, outdoor sofas, chaise lounges and umbrella bases are standard loads. Glass tabletops come off first and travel separately.'),
            ('Can weathered outdoor furniture be donated?', 'Usually not. Sun-faded cushions and rusted or corroded frames are past reuse, so metal goes to recyclers and the rest goes to disposal. Clean indoor furniture is a different story and goes to donation first.'),
            ('Can you take apart shelving, a desk or a bed frame?', 'Yes. Shelving units, desks, bed frames and sectionals come apart as part of the pickup so they clear doors and stairs without damage.'),
            ('Will a narrow street near the lake be a problem?', 'Tell us the layout when you write. Some streets near the water are tighter than the newer additions, and the crew plans the approach before backing the trailer in.'),
            ('How fast can you pick up furniture in The Colony?', 'The Colony is next door to Frisco and Little Elm, so a call before noon typically means the same afternoon. Typical rather than guaranteed, since access and job size are real variables.'),
        ]),
    dict(
        slug='yard-waste-removal-the-colony', kind='yard', city='The Colony', svc='Yard Waste Removal',
        desc='Yard waste removal in The Colony, TX. Storm limbs, brush and old landscaping hauled loose, no bagging, near Lewisville Lake, 7 days a week.',
        lead_hero='Limbs down after a storm, brush piled along the back fence, or landscaping that has aged out. We load it loose from wherever it sits and haul it off the same visit.',
        lead='On the east shore of Lewisville Lake, The Colony gets its share of storm cleanup: limbs down, fence pickets loose, a tree half cleared. The rest is the ordinary work of keeping a yard, from overgrown shrubs to a flower bed being redone. We load loose piles as they sit, no bagging required.',
        involves='Yard waste is rarely one clean category. After a storm, a pile usually mixes limbs, smaller branches, leaves and a few broken fence pickets or deck boards, and we take it as one load rather than asking you to sort it. Outside storm season it is overgrown foundation shrubs coming out, a hedge cut back hard, landscaping timbers and edging from a bed being replaced, or a stack of brush that built up behind the shed. None of it needs to be bagged or bundled first; the crew carries or wheelbarrows loose material straight to the trailer from the backyard, side yard or curb.',
        different='Some streets near the water are tighter than the newer additions further from it, so the crew checks the route in before loading rather than assuming a standard driveway. Tell us about a gate, a shared drive or a narrow side yard when you write. If your pile fits the city&#x27;s own brush collection and you can wait for the date, that is the free option and we will say so. Where we come in is volume and timing: a storm pile you want gone this week, or a yard cleared before a sale. Grass clippings and leaves are also good candidates for a backyard compost pile instead of a haul-off; the ' + EPA + ' covers what works and what does not.',
        more='the main <a href="yard-debris.html">Yard Debris</a> page. And for the rest of what we cover in The Colony, see <a href="junk-removal-the-colony.html">junk removal in The Colony</a>, and for indoor pieces, see <a href="furniture-removal-the-colony.html">furniture removal in The Colony</a>. We run the same crew for <a href="yard-waste-removal-little-elm.html">yard debris pickup in Little Elm</a> and <a href="yard-waste-removal-wylie.html">yard debris pickup in Wylie</a>.',
        faqs=[
            ('Do you take storm debris like limbs and broken fence pickets?', 'Yes. Limbs, branches, loose fence pickets and deck boards are standard loads, and a mixed storm pile goes as one load without sorting.'),
            ('Does the debris need to be bagged before a pickup in The Colony?', NOT_BAGGED),
            ('Should I use the city&#x27;s brush collection instead?', 'If your pile fits the city&#x27;s program and you can wait for the date, yes. We are the option when the pile is too big for it, or when it needs to be gone this week.'),
            ('Can you get to a backyard on a tight street near the lake?', 'Tell us the layout when you write. The crew plans the approach before backing the trailer in, and loose debris can be wheelbarrowed out through a side gate.'),
            ('How fast can you clear a yard debris pile in The Colony?', 'The Colony is next door to Frisco and Little Elm, so a call before noon typically means the same afternoon. Typical rather than guaranteed, since access and job size are real variables.'),
        ]),
    # ------------------------------------------------------------------ Wylie
    dict(
        slug='appliance-pickup-wylie', kind='appliance', city='Wylie', svc='Appliance Pickup',
        desc='Appliance pickup in Wylie, TX. Fridges, freezers, washers, dryers and water heaters carried out beside Lake Lavon and recycled, 7 days a week.',
        lead_hero='A garage freezer that stopped running, a washer and dryer being replaced, or a water heater that finally gave out. We carry it out and route it to recyclers.',
        lead='Wylie has an older core and a lot of newer neighborhoods, and its appliance calls follow the same split: original units in longer-owned houses reaching the end of their run, and working appliances swapped out for an upgrade in newer ones. Either way we handle the simple disconnection, carry the unit out, and send it to a recycler instead of a landfill.',
        involves='The appliance is usually the easy part; the path out is what we plan. A refrigerator has to clear the kitchen opening and the front door, a washer and dryer often come out of a narrow laundry room, and a garage fridge or chest freezer may be wedged behind years of storage. The crew brings an appliance dolly and straps, pads door frames, and handles the basic disconnection on the spot (unplugging, water supply lines, the dryer vent). Gas lines need a licensed plumber to cap them first and hardwired units need an electrician, and we take it from there once that step is done. Units that hold refrigerant, like fridges, freezers and window units, go to certified recyclers who recover it before the steel is reclaimed.',
        different='Wylie sits beside Lake Lavon on the east side of Collin County, the eastern edge of where we go, and a call before noon typically means the same afternoon. A pickup that starts as one dead garage freezer often turns into the old fridge beside it and a few other things that have been waiting, so a photo of the whole garage lets us price it all at once. Working appliances in good condition go to local donation partners first. Anything that leaked out of an old unit, along with paint, fuel and chemicals stored nearby, goes to a household chemical collection program instead of our trailer.',
        more='the main <a href="appliance-removal.html">Appliance Removal</a> page. And for the rest of what we cover in Wylie, see <a href="junk-removal-wylie.html">junk removal in Wylie</a>, and if it is yard debris on the same trip, see <a href="yard-waste-removal-wylie.html">yard waste removal in Wylie</a>. We run the same crew and the same pricing model for <a href="appliance-pickup-mckinney.html">an old fridge or washer in McKinney</a> and <a href="appliance-pickup-dallas.html">an old fridge or washer in Dallas</a>.',
        faqs=[
            ('Can you take a chest freezer or old fridge out of a Wylie garage?', 'Yes. Tell us what is around it. If it is boxed in by storage, the crew clears a path first, and anything else in the garage you want gone can go on the same trip.'),
            ('Do I need to disconnect a water heater before you come?', 'If it is gas, yes: have a licensed plumber cap the gas line first. A hardwired electric unit needs an electrician to disconnect it. Water lines, plug-in units and dryer vents the crew handles on the spot.'),
            ('What happens to an old fridge after a Wylie pickup?', 'Units that hold refrigerant go to certified recyclers who recover it before the metal is reclaimed. Working units in good condition go to local donation partners first.'),
            ('Can you take more than the appliance on the same trip?', 'Yes. Send one photo of everything and you get one firm price for the lot before anything is lifted.'),
            ('How fast can you pick up an appliance in Wylie?', 'Wylie is the eastern edge of our area, and a call before noon typically means the same afternoon. Typical rather than guaranteed, since access and job size are real variables.'),
        ]),
    dict(
        slug='yard-waste-removal-wylie', kind='yard', city='Wylie', svc='Yard Waste Removal',
        desc='Yard waste removal in Wylie, TX. Limbs, brush, shrubs and old landscaping loaded loose, no bagging, and hauled the same visit, 7 days a week.',
        lead_hero='Storm limbs, a brush pile that grew all summer, or shrubs and edging coming out of an old bed. We load it loose from wherever it sits and haul it off the same visit.',
        lead='Wylie mixes an older core with newer neighborhoods, and its yard calls split the same way: mature trees and long-established beds in older yards, and first rounds of landscaping being redone in newer ones. Add the limbs that come down in any North Texas storm season and you have most of what we haul here. We load loose piles as they sit, no bagging required.',
        involves='A yard pickup is usually a mix: cut limbs and branches, brush from a fence line cleared back, shrubs pulled out with their root balls, landscaping timbers, edging and old bagged mulch, sometimes all from the same weekend of work. None of it needs to be bagged or bundled first; the crew carries or wheelbarrows loose material straight to the trailer from the backyard, side yard or curb, and sweeps up the smaller pieces left where the pile sat. A big pile and a small one are quoted the same way, by photo, before anything is lifted.',
        different='Wylie sits beside Lake Lavon on the east side of Collin County, the eastern edge of where we go, and a call before noon typically means the same afternoon. If your pile fits the city&#x27;s own brush collection and you can wait for the date, use it; we would rather tell you the free option exists than take money you did not have to spend. Where we come in is volume and timing: a storm pile you want gone this week, a whole yard being redone, or a cleanup ahead of a sale. Burning yard debris is regulated statewide by the ' + TCEQ + ', so a pickup is often the simpler route. Grass clippings and leaves can also go in a backyard compost pile instead; the ' + EPA + ' covers what works.',
        more='the main <a href="yard-debris.html">Yard Debris</a> page. And for the rest of what we cover in Wylie, see <a href="junk-removal-wylie.html">junk removal in Wylie</a>, and if an old fridge or freezer is going too, see <a href="appliance-pickup-wylie.html">appliance pickup in Wylie</a>. We run the same crew for <a href="yard-waste-removal-allen.html">yard debris pickup in Allen</a> and <a href="yard-waste-removal-the-colony.html">yard debris pickup in The Colony</a>.',
        faqs=[
            ('Do you take shrubs with the root balls still on?', 'Yes. Pulled shrubs, root balls, landscaping timbers and edging are standard loads alongside limbs and brush.'),
            ('Does the debris need to be bagged before a Wylie pickup?', NOT_BAGGED),
            ('Can I just burn the brush pile instead?', 'Outdoor burning in Texas is regulated by the TCEQ, and local rules and burn bans apply on top of that. Check both before lighting anything; hauling it away skips the question.'),
            ('Should I wait for the city&#x27;s brush collection?', 'If your pile fits the city&#x27;s program and you can wait for the date, yes. We are the option when the pile is too big for it, or when it needs to be gone sooner.'),
            ('How fast can you clear a yard debris pile in Wylie?', 'Wylie is the eastern edge of our area, and a call before noon typically means the same afternoon. Typical rather than guaranteed, since access and job size are real variables.'),
        ]),
]


def plain(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s))


def city_obj(city):
    return {'@type': 'City', 'name': city, 'addressRegion': 'TX', 'addressCountry': 'US'}


def jsonld(p, title_short):
    url = '%s/services/%s' % (BASE, p['slug'])
    biz = {'@type': 'LocalBusiness', 'name': 'Hero’s Junk Removal', 'telephone': '(214) 277-9069', 'areaServed': city_obj(p['city'])}
    g = {'@context': 'https://schema.org', '@graph': [
        biz,
        {'@type': 'Service', 'serviceType': '%s in %s, Texas' % (p['svc'], p['city']), 'provider': dict(biz),
         'areaServed': city_obj(p['city']), 'url': url},
        {'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': plain(q), 'acceptedAnswer': {'@type': 'Answer', 'text': plain(a)}} for q, a in p['faqs']]},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': BASE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Services', 'item': BASE + '/services/'},
            {'@type': 'ListItem', 'position': 3, 'name': title_short, 'item': url}]},
    ]}
    return '<script type="application/ld+json">\n%s\n</script>' % json.dumps(g, indent=2, ensure_ascii=False)


def sub1(pattern, repl, s, flags=re.S):
    new, n = re.subn(pattern, lambda m: repl, s, count=1, flags=flags)
    if n != 1:
        sys.exit('pattern not found: %s' % pattern[:80])
    return new


def build(p):
    tpl = (SVC / TEMPLATES[p['kind']]).read_text(encoding='utf-8')
    s = tpl
    short = '%s in %s' % (p['svc'], p['city'])
    title = '%s, TX | Hero’s Junk Removal' % short
    assert len(title) < 60, (title, len(title))
    assert len(p['desc']) <= 160, (p['slug'], len(p['desc']))
    url = '%s/services/%s' % (BASE, p['slug'])
    desc = html.escape(p['desc'], quote=True)

    s = sub1(r'<title>.*?</title>', '<title>%s</title>' % title, s)
    s = sub1(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % desc, s)
    s = sub1(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">' % url, s)
    s = sub1(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="%s">' % title, s)
    s = sub1(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="%s">' % desc, s)
    s = sub1(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="%s">' % url, s)
    s = sub1(r'<meta name="twitter:title" content="[^"]*">', '<meta name="twitter:title" content="%s">' % title, s)
    s = sub1(r'<meta name="twitter:description" content="[^"]*">', '<meta name="twitter:description" content="%s">' % desc, s)
    s = sub1(r'<script type="application/ld\+json">.*?</script>', jsonld(p, short), s)

    # hero
    s = sub1(r'<p class="svc-breadcrumbs">.*?</p>',
             '<p class="svc-breadcrumbs"><a href="../">Home</a> / <a href="./">Services</a> / %s</p>' % short, s)
    s = sub1(r'<h1>.*?</h1>', '<h1>%s in %s, TX</h1>' % (p['svc'][0] + p['svc'][1:].lower(), p['city']), s)
    s = sub1(r'<p class="svc-hero-lead">.*?</p>', '<p class="svc-hero-lead">%s</p>' % p['lead_hero'], s)
    if p.get('photo'):
        ph = PHOTOS[p['photo']]
        st = ph['stem']
        img = ('    <div class="svc-hero-photo">\n'
               '      <div class="video-window" style="aspect-ratio:%s">\n'
               '        <img src="../img/p/%s-820.webp" srcset="../img/p/%s-480.webp 480w, ../img/p/%s-820.webp 820w, ../img/p/%s-1100.webp %s" '
               'sizes="(max-width:1000px) 88vw, 40vw" width="%d" height="%d" alt="%s" loading="eager" fetchpriority="high">\n'
               '        <div class="scrim"></div>\n'
               '      </div>\n'
               '    </div>\n') % (ph['ratio'], st, st, st, st, ph['big'], ph['w'], ph['h'], ph['alt'])
        s = sub1(r'    <div class="svc-hero-photo">.*?\n    </div>\n', img, s)
        s = s.replace('<section class="svc-hero">', '<section class="svc-hero svc-hero--portrait">', 1)

    # body copy
    verb = p['svc'].lower()
    body = ('<div class="svc-content">\n'
            '    <div class="t-sec-head rise"><span class="t-sec-n">(01)</span><span class="t-sec-rule"></span></div>\n'
            '    <h2>%s, %s</h2>\n'
            '    <p class="lead">%s</p>\n\n'
            '    <h2>What a %s pickup actually involves</h2>\n'
            '    <p>%s</p>\n\n'
            '    <h2>What makes %s different</h2>\n'
            '    <p>%s</p>\n\n'
            '%s\n'
            '    <div class="svc-callout"><p><strong>More on %s:</strong> the full walkthrough of how the service works, what is included, and how pricing is quoted lives on %s</p></div>\n'
            '    </div>\n    <aside') % (p['svc'], p['city'], p['lead'], verb, p['involves'], p['city'], p['different'], NUMBER, verb, p['more'])
    s = sub1(r'<div class="svc-content">.*?\n    </div>\n    <aside', body, s)

    # faq
    items = ''.join('      <details><summary>%s</summary><div class="faq-body"><p>%s</p></div></details>\n' % (q, a) for q, a in p['faqs'])
    s, n = re.subn(r'(<div class="faq-list reveal">\n).*?(\n      </div>\n    </div>\n  </div>\n</section>)',
                   lambda m: m.group(1) + items + '    ' + m.group(2), s, count=1, flags=re.S)
    assert n == 1 and items in s, p['slug']
    assert '—' not in s.split('<header', 1)[0] + s.split('<main', 1)[1], p['slug'] + ' has an em dash'
    (SVC / (p['slug'] + '.html')).write_text(s, encoding='utf-8', newline='')
    words = len(plain(re.search(r'<div class="svc-content">(.*?)<aside', s, re.S).group(1)).split())
    print('%-34s %2d-char title  %3d-char desc  %d words  %d faqs' % (p['slug'], len(title), len(p['desc']), words, len(p['faqs'])))


if __name__ == '__main__':
    for p in PAGES:
        build(p)
