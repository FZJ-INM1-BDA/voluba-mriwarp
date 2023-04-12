import os

mriwarp_name = 'voluba-mriwarp'
mriwarp_home = os.path.normpath(os.path.expanduser(f'~/{mriwarp_name}'))
mni_t1_template = os.path.normpath('./data/MNI152_stripped.nii.gz')
mni_t2_template = os.path.normpath('./data/MNI152_T2w_stripped.nii.gz')

# colors
siibra_bg = '#2c2c2c'
siibra_highlight_bg = '#404040'
siibra_fg = '#c4c4c4'
warp_bg = 'black'

# logos
mriwarp_icon = f'./data/{mriwarp_name}.ico'
mriwarp_logo_inv = f'./data/{mriwarp_name}-inv.png'
hbp_ebrains_color = './data/hbp_ebrains_color.png'

# fonts
font_10_b = ('', 10, 'bold')
font_12 = ('', 12, '')
font_12_b = ('', 12, 'bold')
font_18_b = ('', 18, 'bold')

sidepanel_width = 500
