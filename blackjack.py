#!/usr/bin/env python

import time
import curses
import random



SUIT_NAME = ["Hearts", "Spades", "Diamonds", "Clubs"]
CARD_NAME = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
CARD_WIDTH = 18 #width of box to draw card in
CARD_HEIGHT = 9
NUMBER_OF_DECKS = 10 #number of decks to play with
NUMBER_OF_PLAYERS = 2
STARTING_CHIPS = 100

class Card:
	def __init__(self, suit, number):
		self.suit = suit
		self.number = number
		if self.number == 0: #ace
			self.value = 11
		else:
			self.value = 10 if self.number>=9 else self.number + 1
		self.visible = False
	def __str__(self):
		if self.visible:
			return CARD_NAME[self.number] + " of " + SUIT_NAME[self.suit]
		else:
			return "XXXXXXXX"
	def set_ace_as_one(self):
		if self.number == 0 and self.value == 11:
			self.value = 1
			return True
		return False
	def get_value(self):
		return self.value

class Deck:
	def __init__(self, number_of_decks):
		self.number_of_decks = number_of_decks
		self.shuffle_cards()
	def __str__(self):
		strout = ""
		strout += [ str(card) for card in self.cards ]
		return strout
	def shuffle_cards(self):
		self.cards = []
		for k in range(self.number_of_decks):
			for i in range(4): #4 suits
				for j in range(13): #13 cards
					self.cards.append(Card(i, j))
		random.shuffle(self.cards)
	def get_card(self, visible=True):
		try:
			new_card = self.cards.pop()
		except IndexError: #hit the end of the deck, reshuffle
			self.shuffle_cards()
			new_card = self.get_card()
		new_card.visible = visible
		return new_card

class Player:
	def __init__(self, name):
		self.name = name
		self.cards = []
	def __str__(self):
		strout = self.name + ":\n"
		if self.chips > 0:
			strout += "[chips:" + str(self.chips) + "]"
		if self.bet > 0:
			strout += "[bet:" + str(self.bet) + "]"
		if len(self.cards) > 0:
			strout += "[cards: "
			strout += ', '.join([ str(card) for card in self.cards ])
			strout += "]"
			strout += "[card value: " + str(self.get_card_value()) + "]"
		strout += "\n"
		return strout
	def deal_card(self, new_card):
		self.cards.append(new_card)
	def set_ace_as_one(self): #find 1 ace valued at 11 and set it to 1, if we find it then return True, preventing bust
		for card in self.cards:
			if card.set_ace_as_one():
				return True
		return False
	def get_card_value(self):
		card_value = 0
		card_value += sum([ card.get_value() for card in self.cards ])
		if card_value > 21 and self.set_ace_as_one(): #busted, but we have at least 1 ace that was counted as 11. set it to one and return new sum
			return self.get_card_value()
	 	return card_value


class Dealer(Player):
	def __init__(self):
		Player.__init__(self, "Dealer")
		self.revealed = False
		self.status = ""
	def reveal_cards(self):
		self.revealed = True
		for card in self.cards:
			card.visible = True
	def __str__(self):
		strout = self.name + ":\n"
		if len(self.cards) > 0:
			strout += "[cards: "
			strout += ', '.join([ str(card) for card in self.cards ])
			strout += "]"
			strout += "[card value: " + str(self.get_card_value()) + "]"
		strout += "\n"
		return strout
	def draw(self, y, x):
		gui.windows["dealer"].addstr(y,x, self.name)
		gui.windows["dealer"].addstr(y+1,x, ', '.join([ str(card) for card in self.cards ]))
	def draw(self, y, x):
		card_value = str(self.get_card_value())
		gui.dealer_addstr(y, x - 15, self.name)
		if self.revealed:
			gui.dealer_addstr(y + 2, x - 15, "Card value: " + card_value)
		else:
			gui.dealer_addstr(y + 2, x - 15, "Cards:")
		offset = 0
		for card in self.cards:
			gui.draw_rectangle("dealer", y + offset, x, CARD_HEIGHT, CARD_WIDTH)
			gui.dealer_addstr(y + offset + 1, x + 1, str(card))
			gui.dealer_addstr(y + offset + CARD_HEIGHT, x + 1 + CARD_WIDTH - len(str(card)), str(card))
			offset += 2


class HumanPlayer(Player):
	def __init__(self, name, chips=0):
		Player.__init__(self, name)
		self.chips = chips
		self.bet = 0
		self.active = True
		self.status = ""
	def __str__(self):
		strout = self.name + ":\n"
		if self.chips > 0:
			strout += "[chips:" + str(self.chips) + "]"
		if self.bet > 0:
			strout += "[bet:" + str(self.bet) + "]"
		if len(self.cards) > 0:
			strout += "[cards: "
			strout += ', '.join([ str(card) for card in self.cards ])
			strout += "]"
			strout += "[card value: " + str(self.get_card_value()) + "]"
		strout += "\n"
		return strout
	def end_round(self, money_multiplier = 0): #player busted or matched dealer
		self.chips += (self.bet * money_multiplier)
		self.bet = 0
		self.active = False
	def blackjack(self): #player wins
		self.status = "** BLACKJACK **"
		self.end_round(2)
	def win(self): #player wins
		self.status = "** WIN **"
		self.end_round(2)
	def lose(self): #player loses
		self.status = "** LOST **"
		self.end_round()
	def bust(self): #player busts
		self.status = "** BUSTED **"
		self.end_round()
	def push(self):
		self.status = "** PUSH **"
		self.end_round(1)
	def draw(self, y, x):
		card_value = str(self.get_card_value())
		gui.player_addstr(y, x, self.name)
		gui.player_addstr(y + 2, x, "Chips:" + str(self.chips))
		gui.player_addstr(y + 3, x, "Bet:" + str(self.bet))
		gui.player_addstr(y + 4, x, "Card value: " + card_value)
		gui.player_addstr(y + 8, x, self.status, curses.A_REVERSE)
		x_offset = 15
		offset = 0 #6
		for card in self.cards:
			gui.draw_rectangle("players", y + offset, x + x_offset, CARD_HEIGHT, CARD_WIDTH)
			gui.player_addstr(y + offset + 1, x + 1 + x_offset, str(card))
			gui.player_addstr(y + offset + CARD_HEIGHT, x + 1 + CARD_WIDTH - len(str(card)) + x_offset, str(card))
			offset += 2
		


class Game:
	def __init__(self):
		self.players = []
		self.dealer = Dealer()
		for i in range(NUMBER_OF_PLAYERS):
			self.add_player(HumanPlayer("Player " + str(i + 1), STARTING_CHIPS))
		self.deck = Deck(NUMBER_OF_DECKS) # 5 decks
	def __str__(self):
		strout = "#####################################################\n"
		#strout = str(self.deck) + ": "
		strout += str(self.dealer)
		for player in self.players:
			strout += str(player)
		strout += "#####################################################\n"
		return strout
	def add_player(self, player):
		if int(gui.game_width / (25 + CARD_WIDTH)) > len(self.players):
			self.players.append(player)
		else:
			self.draw("Cannot add additional player")
	def ask_bet(self):
		total_active_players = 0
		for player in self.players:
			amount_to_bet = 0
			if not player.active or player.chips <= 0:
				player.active = False
			else:
				while amount_to_bet <= 0 or amount_to_bet > player.chips:
					try:
						amount_to_bet = int(gui.get_input(player.name + ", place your bet [max:" + str(player.chips) + "]:  "))
					except ValueError:
						amount_to_bet = 0
					pass
				player.bet = amount_to_bet
				player.chips -= amount_to_bet
				player.active = True
				total_active_players += 1
			self.draw()
		return total_active_players > 0 #at least 1 player still in the game
	def reset_round(self):
		self.deck = Deck(NUMBER_OF_DECKS)
		self.dealer.cards = []
		self.dealer.revealed = False
		self.dealer.status = ""
		for player in self.players:
			player.cards = []
			player.active = True
			player.status = ""

	def draw(self, message=""):
		try:
			gui.windows["dealer"].clear()
			gui.windows["dealer"].box()
			self.dealer.draw(1,gui.game_width/2 - CARD_WIDTH/2)

			gui.windows["players"].clear()
			gui.windows["players"].box()
			(player_x, player_y) = (2,1) #starting position relative to players window
			for player in self.players:
				player.draw(player_y,player_x)
				player_x += CARD_WIDTH + 25 #leave some space between players
			gui.player_addstr(-10, gui.players_window_x/2 - len(message)/2, message)
			time.sleep(0.4)
		except:
			pass
	def play(self):
		self.reset_round()
		self.draw()
		if not self.ask_bet():
			self.draw("All Players Eliminated")
			return False #break the game loop
		for player in self.players:
			if player.bet > 0:
				player.deal_card(self.deck.get_card())
				self.draw()
		self.dealer.deal_card(self.deck.get_card())
		for player in self.players:
			if player.bet > 0:
				player.deal_card(self.deck.get_card())
				self.draw()
		self.dealer.deal_card(self.deck.get_card(False)) #face down (hidden)
		self.draw()
		if self.dealer.get_card_value() == 21: # dealer has blackjack
			self.dealer.reveal_cards()
			self.draw()
			for player in self.players:
				if player.get_card_value() == 21: # player also has blackjack
					player.push() # refund money
				else:
					player.lose()
		else: #dealer doesn't have blackjack
			for player in self.players: # test for player blackjack
				if player.active and player.get_card_value() == 21:
					player.blackjack()
					self.draw()
			for player in self.players:
				if player.active:
					player.action = ""
					while not player.action in ['S','s'] and player.active:
						double_down = len(player.cards) == 2 and player.chips >= player.bet
						if double_down:
							player.action = gui.get_key(player.name + ", action? [H]it, [S]tand, [D]ouble-down:  ")
						else:
							player.action = gui.get_key(player.name + ", action? [H]it, [S]tand:  ")
						if double_down and player.action in ['D', 'd']:
							player.chips -= player.bet
							player.bet = 2 * player.bet
							player.deal_card(self.deck.get_card())
							player.action = 'S' #force player to stand
							if player.get_card_value() > 21:
								player.bust()
						if player.action in ['H', 'h']:
							player.deal_card(self.deck.get_card())
							if player.get_card_value() > 21:
								player.bust()
						if player.active and player.action in ['S', 's']:
							player.status = "** STAND **"
						self.draw()
			self.dealer.reveal_cards()
			if max([ player.active for player in self.players ]): #if there is at least 1 player still active, otherwise dont bother
				while self.dealer.get_card_value() < 17: #still at least 1 player active, hit until we hit 17
					self.dealer.deal_card(self.deck.get_card())
				self.draw()
				dealer_final_score = self.dealer.get_card_value()
				if dealer_final_score > 21: #dealer bust
					for player in self.players:
						if player.active:
							player.win()
				for player in self.players:
					if player.active:
						player_score = player.get_card_value()
						if player_score < dealer_final_score:
							player.lose()
						elif player_score == dealer_final_score:
							player.push()
						else: #player score is greater than dealer score (but less than 22 because player is still active)
							player.win()
		self.draw()
		key = gui.get_key("Round over. Press any key to continue or q to exit")
		self.draw()
		if key in ['Q','q']:
			return False
		return True

class GUI:
	def __init__(self):
		self.screen = curses.initscr()
		self.screen.immedok(True)
		(self.game_height, self.game_width) = self.screen.getmaxyx()
		#if self.game_height < 60 or self.game_width < 180:
			#print "\x1b[8;60;180t" #resize terminal
			#(self.game_height, self.game_width) = self.screen.getmaxyx()
			#(self.game_height, self.game_width) = (58, 180)
		self.windows = {}
		self.windows["dealer"] = curses.newwin(self.game_height/2-1, self.game_width - 2, 1, 1)
		self.windows["dealer"].immedok(True)
		self.windows["dealer"].box()
		(self.dealer_window_y, self.dealer_window_x) = self.windows["dealer"].getmaxyx()
		self.windows["players"] = curses.newwin(self.game_height - self.dealer_window_y - 1, self.game_width - 2, self.dealer_window_y + 1, 1)
		self.windows["players"].immedok(True)
		self.windows["players"].box()
		(self.players_window_y, self.players_window_x) = self.windows["players"].getmaxyx()
		
	def __del__(self):
		curses.endwin()
	def get_input(self, message = ""):
		self.player_addstr(-3, 2, " " * (len(message) + 10)) #blank out line
		self.player_addstr(-3, 2, message) #,curses.A_REVERSE)
		return self.windows["players"].getstr()
	def get_key(self, message = ""):
		self.player_addstr(-3, 2, " " * (len(message) + 10)) #blank out line
		self.player_addstr(-3, 2, message) #,curses.A_REVERSE)
		return chr(self.windows["players"].getch())
	def player_addstr(self, y, x, message, options=0):
		if (x < 0):
			x = self.players_window_x + x
		if (y < 0):
			y = self.players_window_y + y
		self.windows["players"].addstr(y, x, message, options)
	def draw_rectangle(self, window, y, x, height, width):
		self.windows[window].vline(y + 1, x, curses.ACS_VLINE, height)
		self.windows[window].vline(y + 1, x + width + 1, curses.ACS_VLINE, height)
		self.windows[window].hline(y, x + 1, curses.ACS_HLINE, width)
		self.windows[window].hline(y + height + 1, x + 1, curses.ACS_HLINE, width)
		for i in range(1, height):
			self.windows[window].addstr(y + i, x + 1, " " * width)
		self.windows[window].addch(y, x, curses.ACS_ULCORNER)
		self.windows[window].addch(y, x + width + 1, curses.ACS_URCORNER)
		self.windows[window].addch(y + height + 1, x, curses.ACS_LLCORNER)
		self.windows[window].addch(y + height + 1, x + width + 1, curses.ACS_LRCORNER)
	def dealer_addstr(self, y, x, message, options=0):
		if (x < 0):
			x = self.dealer_window_x + x
		if (y < 0):
			y = self.dealer_window_y + y
		self.windows["dealer"].addstr(y, x, message, options)

if __name__=="__main__":
	round_count = 1
	gui = GUI()
	g = Game()
	while g.play():
		round_count += 1
	del gui
	print "Played a total of " + str(round_count) + " rounds."
	
