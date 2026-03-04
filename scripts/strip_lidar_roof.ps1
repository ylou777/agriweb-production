$f = "static/js/calpinage_3d.js"
$lines = Get-Content $f -Encoding UTF8
Write-Host "Total lines before: $($lines.Count)"

$newBlock = @(
"        // roofPanelsInfo minimal (sera remplace par Solar quand heatmap chargee)",
"        this.roofPanelsInfo = this._computeRoofPanelsInfo(obb, 'flat', 0, bh, terrainH, false, roofType, 1, null);",
"        this.roofPanelsInfo.buildingOBB         = { cx: obb.cx, cz: obb.cz, angle: obb.angle, longDim: obb.longDim, shortDim: obb.shortDim };",
"        this.roofPanelsInfo.buildingTerrainH    = terrainH;",
"        this.roofPanelsInfo.buildingWallH       = bh;",
"        this.roofPanelsInfo.buildingLocalCoords = localCoords.map(c => ({x: c.x, z: c.z}));",
"        if (this.pvBuildingCoords) {",
"            const bCenter = this._polygonCenter(this.pvBuildingCoords);",
"            this.roofPanelsInfo.buildingCenterGeo = { lat: bCenter.y, lng: bCenter.x };",
"        }",
"        // Solar heatmap via applySolarRoofFromInsights() remplacera le cap plat",
"    }"
)

# Lines are 1-based in LineNumber but 0-based in array
# Remove lines 2186..2487 (inclusive, 1-based) => indices 2185..2486
$out = $lines[0..2184] + $newBlock + $lines[2487..($lines.Count-1)]
[System.IO.File]::WriteAllLines((Resolve-Path $f), $out, [System.Text.UTF8Encoding]::new($false))
Write-Host "Total lines after: $($out.Count)"
