from siibra_mriwarp.gui import App
from siibra_mriwarp.logging import setup_logger

if __name__ == '__main__':    
    setup_logger()
    print('Start app')
    try:
        gui = App()
    except Exception as e:
        print(str(e))
    print('Close app')