import scan
import draw

df = scan.box_scan([10, 20], [20, 40], [40, 70])
draw.slice_and_show_strength(df, 'y')
