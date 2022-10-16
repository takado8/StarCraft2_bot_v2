import pickle
import random
from operator import itemgetter

'''
This file is stolen from additional pylons.
Simplified for learning purposes.

Saves the result to find better strats that work.

#{opp_id: [[match_id, strat_id, result, race],]}
{opp_id: [[strat_id, result],]}


'''

class TrainingData:
        
        
        def __init__(self):
                self.results = {}
                self.opp_units = {}
                #load the pickle data.
                self.loadData()

        def saveVictory(self, opp_id, strategy):
                print("opp_id", opp_id)
                print("strategy", strategy)
                self.results.update({opp_id: strategy})
                print("updated victory strategies", self.results)
                #save the results to file.
                self.saveData()

        def saveData(self):
                try:
                        with open("data/res.dat", "wb") as fp:
                                pickle.dump(self.results, fp)
                except (OSError, IOError) as e:
                        print (str(e))

        def loadData(self):
                try:
                        with open("data/res.dat", "rb") as fp:
                                self.results = pickle.load(fp)
                                #print("previous victory strategies", self.results)
                except (OSError, IOError) as e:
                        self.data_dict = {}

        def findStrat(self, opp_id):
                #check if this is a new opponent.
                if not self.results.get(opp_id):
                        #start with random strategy
                        self.new_strategy = True
                        strategy = random.randint(1,10)
                else:
                        strategy = self.results.get(opp_id)
                        print("Last victory came with strategy", strategy)
                if strategy == None:
                        strategy = random.randint(1,10)
                return strategy
        
        def removeResult(self, opp_id):
                #remove the match from the list and save.

                "nothing to be removed -> return"
                if not self.results.get(opp_id):
                        print ('ut oh, where is the match?')
                        return
                self.results.pop(opp_id)
                self.saveData()                         

        "Below this are fuctions that are not used by ANI"





#################
#Data Management#
#################

        def cleanStrat(self, opp_id, strat_id, map_name):
                opp_data = [x for x in self.data_dict.get(opp_id) if x[1] == strat_id]
                opp_data = sorted(opp_data, key=itemgetter(0), reverse=True)
                del opp_data[4:]
                #remove existing data for the strat_id and create a new list for the dictionary.
                old_data = self.data_dict.get(opp_id)
                for match in old_data:
                        if match[1] != strat_id:
                                #not the strat being cleaned, add the match.
                                opp_data.append(match)
                self.data_dict.update({opp_id:opp_data})
                #save the results to file.
                self.saveData()
                       
        def getOppHistory(self, opp_id, race):
                #opp_id = "{}-{}".format(race, str(opp_id))
                return self.opp_units.get(opp_id)
        
        def saveUnitResult(self, opp_id, units, race):
                #opp_id = "{}-{}".format(race, str(opp_id))
                #only saving the last games units, so always just overwrite the previous.
                self.opp_units.update({opp_id:units})
                #now save it.
                self.saveUnitsData()
                
                
        
#################
#File Management#
#################


        def saveUnitsData(self):
                with open("data/unitRes.dat", "wb") as fp:
                        pickle.dump(self.opp_units, fp)         

                try:
                        with open("data/unitRes.dat", "rb") as fp:
                                self.opp_units = pickle.load(fp)
                except (OSError, IOError) as e:
                        self.opp_units = {}
                

########
#Others#
########

        def stratWinPer(self):
                if self.first_game:
                        return " I have no opponent data, so this is a good starting point."
                elif self.random_choice:
                        return " I need more data, so I'm choosing randomly."
                else:
                        return ' I win with it {}% of the time lately.'.format(self.best_win_per)

                

        def totalOppDataCount(self, opp, race):
                #opp = "{}-{}".format(race, str(opp))
                if self.data_dict.get(opp):
                        return len(self.data_dict.get(opp))     
                return 0


        def totalDataCount(self):
                total = 0
                for opp, matches in self.data_dict.items():
                        total += len(matches)
                return total


