import motormag

df = motormag.scan.box_scan([10, 20], [20, 40], [40, 70], n_discards=0)
motormag.draw.strength_2d(df, 'y')
