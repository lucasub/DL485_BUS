from datetime import datetime
import colorama
from colorama import Fore, Style
import logging




class Log:
    """
    LOG class
    Set logstate:
        0: not write any log
        1: print on screen
        2: write on file
        3: write on screen and file
    Pass file_name
    """
    
    col = {
       'BLACK':     30,
       'RED':       31,
       'GREEN':     32,
       'YELLOW':    33,
       'BLUE':      34,
       'MAGENTA':   35,
       'CYAN':      36,
       'WHITE':     37,
       'RESET':     39,
    }

    def __init__(self, logstate, file='log.txt'):
        # print("LOGSTATE: ", logstate)
        self.logstate = logstate
        if self.logstate & 1:
            self.file = file
            logging.basicConfig(format='%(asctime)s %(message)s',
                                datefmt='%m/%d/%Y %H:%M:%S',
                                filename=self.file,
                                level=logging.DEBUG)

    def writelog(self, data='', color='WHITE'):
        """
        Write log to file or screen
        """
        if self.logstate & 1:
            logging.debug(f'data')  # Write LOG to file
        if self.logstate & 2:
            print(f'\033[{self.col[color]}m{datetime.now()}m {data}')  # Show log to terminal


if __name__ == '__main__':
    print("TEST LOG Class")
    log = Log(2, 'test_log.txt')
    log.writelog("Test Log")
