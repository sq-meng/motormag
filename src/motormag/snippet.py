import scan
import draw

df = scan.box_scan([10, 20], [20, 40], [40, 70])
draw.strength_2d(df, 'y')
