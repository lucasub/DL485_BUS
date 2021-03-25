from datetime import datetime
import logging

class Log:
    """
    LOG class
    Pass file_name
    Set logstate:
        0: not write any log
        1: print on screen
        2: write on file
        3: write on screen and file
    """

    def __init__(self, file='log.txt', logstate=0):
        self.logstate = logstate
        if self.logstate & 1:
            self.file = file
            logging.basicConfig(format='%(asctime)s %(message)s',
                datefmt='%m/%d/%Y %H:%M:%S',
                filename=self.file,
                level=logging.DEBUG)

    def write(self, data=''):
        """
        Write log to file or screen
        """
        if self.logstate & 1:
            logging.debug(f'data')  # Write LOG to file
        
        if self.logstate & 2:
            print(f'{datetime.now()} {data}')  # Show log to terminal

if __name__ == '__main__':
    log = Log('test_log.txt', 1) 
    log.write("Test Log")