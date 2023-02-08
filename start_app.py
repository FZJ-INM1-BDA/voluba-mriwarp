from siibra_mriwarp.gui import App

if __name__ == '__main__':
    try:
        gui = App()
    except Exception as e:
        print(str(e))
