import player_select
import game

def main():
    num_players = player_select.run_player_select()
    game_instance = game.Game(num_players)
    game_instance.run()

if __name__ == "__main__":
    main()