import sys
import time
import paho.mqtt.client as Client
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

"""
Bot for telegram
"""
import telepot
from telepot.loop import MessageLoop
import time
from pprint import pprint

class TelBot:
    def __init__(self, token, get_board_type, mapiotype, status):
        self.get_board_type = get_board_type
        self.mapiotype = mapiotype
        self.telegram_token = token
        self.status = status
        self.telegram_bot = False


    def init_bot(self):
        """ Telegram BOT """
        print("Bot Telegram begin")
        self.telegram_bot = telepot.Bot(self.telegram_token)
        # print(dir(self.telegram_bot))
        # MessageLoop(self.telegram_bot, self.handle).run_as_thread()
        self.telegram_bot.message_loop({
            'chat': self.on_chat_message,
            'callback_query': self.on_callback_query,
            'inline_query': self.on_inline_query,
            'chosen_inline_result': self.on_chosen_inline_result,
        })

    def on_chosen_inline_result(self, msg):
        result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
        print ('Chosen Inline Result:', result_id, from_id, query_string)


    def on_inline_query(self, msg):
        query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
        print ('Inline Query:', query_id, from_id, query_string)

        articles = [InlineQueryResultArticle(
                        id='abc',
                        title='ABC',
                        input_message_content=InputTextMessageContent(
                            message_text='Hello'
                        )
                )]

        self.telegram_bot.answerInlineQuery(query_id, articles)

    def on_chat_message(self, msg):
        
        content_type, chat_type, chat_id = telepot.glance(msg, flavor="chat")
        # self.chat_id = chat_id
        # print(content_type)
        chat_id = msg['chat']['id']
        # print("------------", chat_id, chat_id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                   [InlineKeyboardButton(text='INFO Domocontrol', callback_data='info')],
               ])

        # self.telegram_bot.sendMessage(chat_id, 'Use inline keyboard', reply_markup=keyboard)

        nameuser = msg['chat']['first_name']
        print("Telegram Nome User:", nameuser)
        if content_type != 'text':
            self.telegram_bot.sendMessage(chat_id, 'Ammesso solo TESTO')
            return
        command = msg['text']
        print("telegram_bot Command:", command)


        msg = ''
        if command == '/INFO':
            msg = self.info(nameuser)
        elif command == '/BOARD':
            # pprint(status)
            msg = self.board()
        elif '/BOARD' in command:  # /BOARDx_io
            msg = self.boardx_io(command[1:])
        elif '/B' in command and 'IO' in command:
            msg = self.gpio(command[1:])
        else:
            print("Command not valid")

        # elif command == '/BOARD_TYPE':
        #     for board_id in self.get_board_type.keys():
        #         msg = "/BOARD_TYPE_{}".format(board_id)
        #         self.telegram_bot.sendMessage(chat_id, msg)

        # elif '/BOARD_TYPE_' in command:
            # board_id = int(command[12:])
            # msg = f"/BOARD_TYPE \n /BOARD_ID_{board_id}\n"
            # msg += f"Board Type: \
            #     {self.get_board_type[board_id]['board_type']}\n"
            # msg += f"Data Firmware: \
            #     {self.get_board_type[board_id]['data_firmware']}\n"
            # msg += f"I/O Numbers: \
            #     {self.get_board_type[board_id]['io_number']}\n"
            # msg += f"I2C: {self.get_board_type[board_id]['i2c']}\n"
            # msg += f"One Wire: {self.get_board_type[board_id]['onewire']}\n"
            # msg += f"PLC: {self.get_board_type[board_id]['plc']}\n"
            # msg += f"Power On: {self.get_board_type[board_id]['power_on']}\n"
            # msg += f"PWM: {self.get_board_type[board_id]['pwm']}\n"
            # msg += f"RFID: {self.get_board_type[board_id]['rfid']}\n"
            # msg += f"PRO: {self.get_board_type[board_id]['protection']}\n"
            # # print(self.get_board_type[board_id])
            # self.telegram_bot.sendMessage(chat_id, msg)

        # elif '/BOARD' in command:  # MOstra board presenti sul bus
        #     # print(command)
        #     bid = int(command[6:])
        #     res = 'I/O della Board {}\n'.format(command)
        #     # lendict = len(self.mapiotype[bid])
        #     for n in self.mapiotype[bid]:
        #         # pprint(self.mapiotype[bid][n])
        #         # pprint(self.status[bid]['io'])
        #         # dtype = self.mapiotype[bid][n]['dtype']
        #         name = self.mapiotype[bid][n]['name']
        #         logic_io = int(self.mapiotype[bid][n]['logic_io'])
        #         value = self.status[bid]['io'][logic_io - 1]
        #         device_type = self.mapiotype[bid][n]['device_type']
        #         # print(command, bid, logic_io, name, value)
        #         add_slash = ' '
        #         if device_type in ['DIGITAL_OUT']:
        #             value &= 1
        #             add_slash = '/'
        #         res += f'{add_slash}{bid}_{logic_io} {name} {value}\n'
        #     self.telegram_bot.sendMessage(chat_id, res)

        # elif '_' in command and '/' in command:  # Setta I/O
        #     # print(command)
        #     bl = command[1:].split("_")
        #     bid = int(bl[0])
        #     logic_io = int(bl[1])
        #     value = self.status[bid]['io'][logic_io - 1] & 1
        #     value_new = 1 - value
        #     res = "/BOARD{} : Cambia il valore dell'uscita\n".format(bid)
        #     res += '/{}_{}  {} => {}'.format(bid, logic_io, value, value_new)
        #     cmd = self.writeIO(bid, logic_io, [value_new])
        #     # print(cmd)
        #     self.TXmsg.append(cmd)
        #     self.telegram_bot.sendMessage(chat_id, res)

        # elif '_' in command:  # Setta I/O
        #     # print(command)
        #     board_id, logic_io = command[1:].split('_')
        #     board_id = int(board_id)
        #     logic_io = int(logic_io)
        #     # print(board_id, logic_io)
        #     pprint(self.mapiotype[board_id][logic_io])

        #     keyboard = InlineKeyboardMarkup(inline_keyboard=[
        #         [InlineKeyboardButton(text='Press me', callback_data='press')],
        #         ])
        #     self.telegram_bot.sendMessage(chat_id, '-', reply_markup=keyboard)

        # elif command == '/R':
        #     self.telegram_bot.sendMessage(
        #       chat_id, 'Leggi il valore di un I/O - Da Fare')
        # elif command == '/S':
        #     self.telegram_bot.sendMessage(
        #       chat_id, 'Scrivi il valore di un I/O - Da Fare')
    #     else:
    #         self.telegram_bot.sendMessage(chat_id, """commandi disponibili:
    # /INFO (informazioni)
    # /BOARD (info board presenti)
    #         """)

        # return msg + self.general_command()

        self.telegram_bot.sendMessage(chat_id, msg + self.general_command(), parse_mode='HTML')

    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(
            msg, flavor='callback_query')
        print('Callback Query:', query_id, from_id, query_data)
        self.telegram_bot.answerCallbackQuery(query_id, text='Domocontrol System')   
    
    def general_command(self):
        msg = "\n<b>Comandi disponibili:</b>\n"
        msg += "/INFO (informazioni)\n"
        msg += "/BOARD (info board presenti)\n"
        return msg

    def info(self, nameuser):
        msg = f"\n<b>Ciao {nameuser}</b>\n"
        msg += "<b>Telegram Bot per Domoticz</b>\n"
        msg += "Interfaccia per intergire con DL485 Board,\n"
        msg += "schede per la Domotica su BUS RS485.\n"
        msg += "Autori: Luca e Daniele\n"
        msg += "Info su <a href='https://www.domocontrol.info/domotica'>DOMOCONTORL</a>\n"
        return msg

    def board(self):
        msg = '\n<b>Board on CONFIG</b>\n'
        for s in self.status:
            if s <=9: #  Alignment font
                l1 = "   "
            else:
                l1 = " "
            msg += '/BOARD{} {} enable: {:^3}   type: {}\n'.format(s, l1,  self.status[s]["boardenable"], self.status[s]["boardtypename"], )
        return msg

    def dunit(self, bid, io):
        dunit = ''
        if self.mapiotype[bid][io]['dunit'] != None:
            dunit = self.mapiotype[bid][io]['dunit']
        elif self.mapiotype[bid][io]['device_type'] == 'TEMP_ATMEGA':
            dunit = '°C'
        elif self.mapiotype[bid][io]['device_type'] in ['VINR1R2',]:
            dunit = 'V'
        elif self.mapiotype[bid][io]['device_type'] in ['DIGITAL_OUT']:
            dunit = ''
        elif self.mapiotype[bid][io]['dtype'] == 'Current (Single)':
            dunit = 'A'
        elif self.mapiotype[bid][io]['dtype'] == 'Voltage':
            dunit = 'V'
        elif self.mapiotype[bid][io]['dtype'] == 'kWh':
            dunit = 'kW'
        elif self.mapiotype[bid][io]['dtype'] == 'Temperature':
            dunit = '°C'
        else:
            # pprint(self.mapiotype[bid][io])
            print(f"==>> DUNIT not implemented {bid}-{io} {self.mapiotype[bid][io]['device_type']} {dunit}")
        return dunit

    def boardx_io(self, command):
        bid = int(command[5:])
        msg = f'<b>Caracteristics of {command}</b>\n'
        msg += f'Type:{self.status[bid]["boardtypename"]} enable:{self.status[bid]["boardenable"]} \n'
        for io in self.mapiotype[bid]:
            if io <=9: #  Alignment font
                l1 = "   "
            else:
                l1 = " "
            # pprint(self.mapiotype[bid][io])
            
            msg += f'/B{bid}IO{io}{l1}   {self.status[bid]["io"][io - 1]} {self.dunit(bid, io)} - {self.mapiotype[bid][io]["name"]} \n'
        return msg

    def gpio(self, command):
        bid = int(command[1:command.find('IO')])
        io = int(command[command.find('IO')+2:])
        print(command, bid, io)
        m = self.mapiotype[bid][io]
        pprint(m)

        msg = f'/BOARD{bid} - IO{io}\n'
        msg += f'{m["name"]}\n{m["description"]} \n\n'
        msg += f'Value:        {self.status[bid]["io"][io - 1]} {self.dunit(bid, io)}\n'
        msg += f'Enable:       { self.mapiotype[bid][io]["enable"] }\n'
        msg += f'Device Type:  { self.mapiotype[bid][io]["device_type"] }\n'
        msg += f'Time Refresh: { int(self.mapiotype[bid][io]["time_refresh"]/10) } Sec.\n'
        

        return msg
