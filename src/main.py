import player_select
import make_game_field

def main():
    num_players = player_select.run_player_select()
    game = make_game_field.Game(num_players)
    game.run()

if __name__ == "__main__":
    main()