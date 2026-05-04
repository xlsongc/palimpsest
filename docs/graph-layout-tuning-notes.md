# Graph Layout Tuning Notes

These notes capture the next tuning baseline for the D3 reading graph.

## Current Direction

- Keep the graph naturally spread rather than force-clustered into fixed theme centers.
- Avoid static background theme circles; theme regions should emerge from D3-computed node positions.
- Keep read, reading, and want visually comparable. Distinguish status mostly by stroke, dash, fill opacity, and color rather than large size differences.

## Candidate Force Parameters

Use these as the next experiment baseline:

```js
// Link force: controls distance between connected books.
.force("link")
  .distance(d => 45 + (5 - d.strength) * 18)
  .strength(0.48)

// Charge force: pushes unrelated nodes apart.
.force("charge")
  .strength(-70)
  .distanceMax(200)

// Center force: keeps the graph inside the viewport.
.force("center")
  .strength(0.08)

// Collision force: prevents node overlap.
.force("collide")
  .radius(d => nodeRadius(d) + 12)
```

## Adjustment Rules

- More compact: move charge from `-70` toward `-50`, or reduce `distanceMax` from `200` toward `150`.
- More spread out: move charge toward `-120`, or remove `distanceMax`.
- Clearer theme separation: increase `distanceMax` to `300+`.
- Connected books closer: reduce link distance, or increase link strength toward `0.6+`.

## Initial Positioning

For future experiments, seed initial positions by theme angle around the graph center:

- Radius range: `25px` to `80px`.
- Smaller radius creates a calmer initial settle.
- Larger radius makes the graph start more spread out.
