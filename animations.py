


tank = '''░░░░░░███████ ]▄▄▄▄▄▄▄▄▃
▂▄▅█████████▅▄▃▂        
I███████████████████].  
◥⊙▲⊙▲⊙▲⊙▲⊙▲⊙▲⊙◤...      
'''


rev_tank = '\n'.join([line[::-1] for line in tank.split('\n')])

print(rev_tank)




def get_space( width=80, perc=0.):
    d = round(float(perc)/width)
    line = '\n'.join( 4*[' '*width])
    line[d] = '*'
    return line



def plot_tanks( width=80, perc=0., left_to_right=True):

    # cannon ball position
    d = min( round(perc*width), width-1)
    if not left_to_right:
        d = width - 1 - d 
    print(d)
    
    anim = []
    for cc, line in enumerate( tank.split('\n')):

        spaces = width*[' ']
        if cc==0:
            spaces[d] = '*'
        
        
        anim.append( line + ''.join(spaces) + line[::-1])
    
    return '\n'.join(anim)


        
import time

for pp in range(0,101):
    print(
        plot_tanks( width=60, perc=pp/100., left_to_right=False)
    )
    time.sleep(.01)

