# shcalpy
Calibrate your Shapeoko-3 with its aluminum table

## Introduction

I bought Carbide3D's Shapeoko 3 desktop milling machine, not knowing anything about milling or machining.  I thought it would be an interesting hobby.

After a friend and I assembled it, I set about researching how to “program” it.  I found Autodesk's Fusion 360 and fell in love with it.  Apart from the ease of design, it's output can be directly used by the  Shapeoko 3 without any file conversions.

I made quite a few small projects, building up my knowledge and skills along the way.  All milling is done within a coordinate system relative to an origin defined for the piece.  The piece is held firmly in place to the Shapeoko's HDF table.

As I progressed, I noticed a minor problem in that when milling a flat surface, the tool bit would cut into one side of a flat 1 inch thick piece before the other.  Since the piece was firmly clamped to the table, this meant that the table was not parallel to the plane that the bit traveled.  This would translate to a 0.25 mm (0.01 in) difference in thickness over a 150 mm (6 in) distance.

When attempting to mill 2-sided projects, I encountered a problem that was also difficult to solve.  These projects involve milling, say, the bottom (and inside) of a piece and then flipping it over complete the machining of the top (and outside).  This is not as easy as it seems, particularly if you want the machining of holes to line up on both sides of the piece.  My attempts often had these holes misaligned by 1 mm or more, even with my best efforts.

When making a 2-sided piece, each side will have its own coordinate system and origin.  And when flipping it to machine the other side, everything is so much simpler if the axis of rotation is along some “center line” of the piece.  Fusion 360 makes this easy, but flipping the piece itself precisely and accurately along the center line is difficult.  When flipping a piece to mill the other side, I found I could not align the axis of rotation parallel to the center line with reliable accuracy.

I wanted to solve these problems to produce higher quality work.

The solution involved these steps:
1. Purchasing and installing an aluminum threaded table from Carbide3D.  This table has holes with 50 mm spacing.
2. Designing and milling a depth gauge mount, suitable to electrically measure whether or not it is touching the aluminum table at various Z values of the Shapeoko.
3. Wiring up a Raspberry Pi to the table and depth gauge.
4. Writing a Python program to traverse the table gathering X, Y, and Z measurements, calculate the least squares fit of the plane matching the measurements, and the corrections needed at the table's mounting points.
5. Leveling the table, using folded aluminum foil.
6. Writing a Python program to measure the holes locations, and calculate the equations of the hole rows and columns to determine their orientation relative to the tool X and Y axes.
7. Discovering that the gears controlling the tool Y position (on the left and right sides) were slightly but significantly different sizes, and replacing them with gears that were equal-sized.  Without this, the table's holes on the same row aren't really parallel to the other rows as measured by the tool tip.
8. Designing an X-Y axis "power-on alignment tool" to be used when powering on the Shapeoko (a precisely straight piece of wood).  The Shapeoko gantry, the bridge-like structure that holds the router or other tool, has independent stepper motors and gears on either side.  When powered off, the gantry has some slop.  Powering up with the gantry while it's held against this power-on alignment tool sets it to a known position.
9. Determining the offset to be used with the power-on alignment tool, so that the rows of holes are parallel to the gantry X-axis movement.


## What you will need

I'm assuming you know your Shapeoko and have some electronics skills.

### You've probably already got this...

1. [Shapeoko-3 desktop milling machine](https://shop.carbide3d.com/products/shapeoko3?variant=42721918086)
2. Upgrade the Shapeoko to have the [homing switches](https://shop.carbide3d.com/collections/tools/products/shapeoko-3-limit-switch-kit?variant=42747504070) if it didn't come with them. 
3. Upgrade the [Shapeoko PCB to support GRBL 1.1](https://shop.carbide3d.com/collections/replacement-parts/products/carbide-motion-pcb?variant=16688468102). My PCBA is labeled CarbideMotion 2.4e.  [controller firmware info](http://docs.carbide3d.com/shapeoko-faq/controller-firmware-information/)

### Electronics and tools for doing the measurements...

4. Raspberry Pi with power supply, USB Cable, keyboard, mouse, monitor and cable
5. Several feet of 26 AWG wire, two 1200 ohm resistors, ability to wire up a [simple circuit](/Pictures/ShapeokoCircuit.png)
6. iGaging Depth Gauge (Item# 400-D69) or equivalent
7. HDPE, LDPE or ABS: 1" thick, to make the mount for the depth gauge 
8. Either ABS glue or 4 screws & nuts to put the depth gauge and its mount together

### Stuff used to level the Shapeoko table, and align it when it is powered on

9. Tin foil
10. Hard wood stick, mine is 627 mm long 8.7 mm x 18.75 mm.
11. Spark plug feeler gauge

## What to do:



