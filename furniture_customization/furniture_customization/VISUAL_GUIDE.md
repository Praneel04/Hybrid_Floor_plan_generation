# 🎨 Furniture Placement UI - Visual Guide

```
╔════════════════════════════════════════════════════════════════════════════╗
║                   FURNITURE PLACEMENT DESIGNER                              ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────┬────────────────────────────────────────┬─────────────┐
│   SIDEBAR           │       MAIN CANVAS                      │  INFO PANEL │
│                     │                                        │             │
│ ┌─────────────────┐ │  ┌──────────────────────────────────┐ │ ┌─────────┐ │
│ │ 📐 Load Floor   │ │  │                                  │ │ │ 🚪 Room │ │
│ │    Plan         │ │  │     🏠 FLOOR PLAN                │ │ │   Info  │ │
│ └─────────────────┘ │  │                                  │ │ └─────────┘ │
│                     │  │   ┌─────────────────┐            │ │             │
│ 📦 Bedroom          │  │   │ bedroom_1       │            │ │ • bedroom_1 │
│  ├─ Bed ➕          │  │   │  56.3 m²        │            │ │   56.3 m²   │
│  ├─ Bedside ➕      │  │   └─────────────────┘            │ │             │
│  └─ Single bed ➕   │  │                                  │ │ • bathroom  │
│                     │  │   ┌───────────────────────────┐  │ │   58.2 m²   │
│ 📦 Living Room      │  │   │   living_room_1           │  │ │             │
│  ├─ Sofa ➕         │  │   │   394.4 m²                │  │ │ 📊 Stats   │
│  ├─ L-sofa ➕       │  │   │                           │  │ │             │
│  ├─ Chair ➕        │  │   │   [Bed] ───────┐          │  │ │ Total: 3   │
│  └─ TV ➕           │  │   │        │        │          │  │ │            │
│                     │  │   │        └────────┘          │  │ └──────────┘ │
│ 📦 Kitchen          │  │   │                           │  │              │
│  ├─ Stove ➕        │  │   └───────────────────────────┘  │              │
│  └─ Sink ➕         │  │                                  │              │
│                     │  │   📍 Manual Placement:           │              │
│ 📋 Placed Items     │  │   X: [150] Y: [200] [Place]     │              │
│  1. Bed (bedroom)🗑️ │  └──────────────────────────────────┘              │
│  2. Sofa (living)🗑️ │                                                    │
│  3. Table (dining)🗑️│                                                    │
│                     │                                                     │
│ [🧹 Clear All]      │                                                     │
│ [💾 Save Layout]    │                                                     │
└─────────────────────┴─────────────────────────────────────────────────────┘

╔════════════════════════════════════════════════════════════════════════════╗
║                            WORKFLOW STEPS                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

   STEP 1              STEP 2              STEP 3              STEP 4
   ┌─────┐            ┌─────┐            ┌─────┐            ┌─────┐
   │  📐 │ ────────>  │  🛋️ │ ────────>  │  📍 │ ────────>  │  💾 │
   └─────┘            └─────┘            └─────┘            └─────┘
   Load Floor         Select             Place on           Save
   Plan               Furniture          Canvas             Layout


╔════════════════════════════════════════════════════════════════════════════╗
║                          BOUNDARY VALIDATION                                ║
╚════════════════════════════════════════════════════════════════════════════╝

  ✅ VALID PLACEMENT              ❌ INVALID PLACEMENT
  ┌─────────────────┐            ┌─────────────────┐
  │  Room           │            │  Room    ┌────┐ │
  │                 │            │          │ ❌ │ │ ← Outside boundary
  │   ┌──────┐      │            │          └────┘─┘
  │   │  ✅  │      │            │                 │
  │   └──────┘      │            └─────────────────┘
  │    Bed          │            
  └─────────────────┘            


╔════════════════════════════════════════════════════════════════════════════╗
║                         FURNITURE CATEGORIES                                ║
╚════════════════════════════════════════════════════════════════════════════╝

┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│   Bedroom    │ Living Room  │   Kitchen    │  Bathroom    │ Dining/Study │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ • Bed        │ • Sofa       │ • Stove      │ • Bathtub    │ • Dining     │
│ • Single bed │ • L-sofa     │ • Sink       │ • Shower     │   table      │
│ • Bedside    │ • Chair      │ • Kitchen    │ • Commode    │ • Study      │
│              │ • TV         │              │ • Sink       │   table      │
│              │ • Table      │              │              │ • Chair      │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘


╔════════════════════════════════════════════════════════════════════════════╗
║                           EXAMPLE LAYOUTS                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

    BEDROOM LAYOUT              LIVING ROOM LAYOUT          BATHROOM LAYOUT
    ┌─────────────┐             ┌──────────────────┐        ┌──────────┐
    │  ┌────────┐ │             │  ┌────┐          │        │ ┌──────┐ │
    │  │  Bed   │ │             │  │ TV │          │        │ │Tub   │ │
    │  └────────┘ │             │  └────┘          │        │ └──────┘ │
    │             │             │                  │        │          │
    │  [B][B]     │             │  ┌────────────┐  │        │   [S]    │
    │   ^  ^      │             │  │  L-Sofa    │  │        │          │
    │Bedside tables│            │  └────────────┘  │        │   [C]    │
    └─────────────┘             └──────────────────┘        └──────────┘


╔════════════════════════════════════════════════════════════════════════════╗
║                         CONTROL REFERENCE                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

┌────────────────────────┬──────────────────────────────────────────────────┐
│      ACTION            │               HOW TO DO IT                       │
├────────────────────────┼──────────────────────────────────────────────────┤
│ Load floor plan        │ Click "📐 Load Floor Plan" button                │
│ Select furniture       │ Click "➕" next to furniture item                │
│ Place furniture        │ Enter X, Y coordinates and click "📍 Place"      │
│ Remove item            │ Click "🗑️" next to placed item                   │
│ Clear all furniture    │ Click "🧹 Clear All" button                      │
│ Save layout            │ Click "💾 Save" button                           │
│ Cancel selection       │ Click "❌ Cancel Selection" button               │
│ View room info         │ Expand room in info panel                        │
└────────────────────────┴──────────────────────────────────────────────────┘


╔════════════════════════════════════════════════════════════════════════════╗
║                         SUCCESS INDICATORS                                  ║
╚════════════════════════════════════════════════════════════════════════════╝

✅ Furniture placed successfully        → Green box around furniture
✅ Room boundary visible                → White outline on floor plan
✅ Furniture fits in room              → Success message displayed
✅ Layout saved                        → "Layout saved!" message

❌ Cannot place outside boundary       → Error message shown
❌ Furniture doesn't fit               → Placement rejected
❌ No furniture selected               → Place button disabled


╔════════════════════════════════════════════════════════════════════════════╗
║                         KEYBOARD SHORTCUTS                                  ║
╚════════════════════════════════════════════════════════════════════════════╝

• Ctrl/Cmd + R     → Refresh the application
• Tab              → Navigate between fields
• Enter            → Submit form/place furniture
• Escape           → Close expanded panels


╔════════════════════════════════════════════════════════════════════════════╗
║                         OUTPUT FILES                                        ║
╚════════════════════════════════════════════════════════════════════════════╝

📄 furniture_layout.json     → Layout data (positions, dimensions, rooms)
🖼️  furniture_layout.png      → Visual representation with furniture

Example JSON structure:
{
  "furniture": [
    {
      "name": "Bed",
      "position": [150, 200],
      "dimensions": {"width_m": 6.8, "height_m": 7.9},
      "room": "bedroom_6"
    }
  ]
}


╔════════════════════════════════════════════════════════════════════════════╗
║                         TIPS & TRICKS                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

💡 Start with large furniture (beds, sofas) first
💡 Check room dimensions before selecting furniture
💡 Use categories to find appropriate furniture for each room
💡 Place functional items (beds, tables) before decorative items
💡 Save frequently to preserve your work
💡 Try different layouts - removal is easy!
💡 Use the info panel to track furniture per room
💡 Pay attention to error messages for placement issues


╔════════════════════════════════════════════════════════════════════════════╗
║                         ROOM SPECIFICATIONS                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────┬─────────┬────────────────────────────────────────────────┐
│ Room            │ Area    │ Recommended Furniture                          │
├─────────────────┼─────────┼────────────────────────────────────────────────┤
│ Living Room 1   │ 394.4m² │ Large sofa, TV, multiple tables, chairs       │
│ Bedroom 6       │ 187.2m² │ King bed, bedside tables, wardrobe            │
│ Bedroom 5       │  69.7m² │ Queen bed, bedside table                       │
│ Bathroom 1      │  58.2m² │ Bathtub, sink, commode, shower                │
│ Bedroom 1       │  56.3m² │ Single/double bed, small table                │
│ Bathroom 3      │  42.9m² │ Shower, sink, commode                         │
└─────────────────┴─────────┴────────────────────────────────────────────────┘

```
