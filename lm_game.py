import pyxel
import random
import math
from collections import defaultdict

WINDOW_W = 160
WINDOW_H = 120
UI_HEIGHT = 35
PLAYER_SPEED = 2.0
BULLET_SPEED = 5.0
TOKEN_SPEED = 1.0
TOKEN_SPAWN_INTERVAL = 60

# Utility functions
def create_corpus():
    sentences =  """The cat sat on the bed.
I read a book last week.
He ran fast in the park.
She made a cake for me.
The dog barked all day.
We sang songs by the fire.
They went to play in the sun.
She saw a bird on the tree.
He likes fish and soup.
I swam in the cool lake.
The kids made a sand fort.
He gave me a gift box.
They love to hike and run.
The bus was late last time.
I like rice and hot tea.
The frog sat on a rock.
She put jam on her roll.
The moon is big and bright.
I lost my hat in the wind.
He made a plan to go out.
The sun was warm and bright.
We ran to the top of the hill.
He lost his hat in the park.
She gave me a hug last night.
The fish swam fast in the pond.
I sat on the deck with my dog.
They sang a song by the fire.
The book is on the desk now.
He ate the last of the cake.
She made tea for her mom.
I like to play games with him.
The car was red and very fast.
She held a big box for me.
He told me a joke last time.
They went to the mall to shop.
The bird flew up to the tree.
I gave her a doll for her toy.
The kids are out in the yard.
He put the book in the bag.
She sat in the sun with a hat.
We saw a fox run in the woods.
The boat sank fast in the lake.
She took a nap on the couch.
He likes to fish in the pond.
The dog dug a hole in the yard.
I made soup with rice and meat.
We ate the last bit of the pie.
She put jam on her slice of bread.
The stars are out in the sky now.
He said yes to my new plan."""
    return " ".join(sentences.lower().replace(".", "").split("\n"))

CORPUS = create_corpus()
HEAD_WORDS = [sentence.split()[0] for sentence in CORPUS.split("\n")]
FAKE_WORDS = CORPUS.split()


def draw_big_text(x, y, text, text_col=10, outline_col=0):
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            pyxel.text(x + dx, y + dy, text, outline_col)
    pyxel.text(x, y, text, text_col)


def train_bigram_model(corpus):
    words = corpus.split()
    bigram_freq = defaultdict(lambda: defaultdict(int))
    for w1, w2 in zip(words, words[1:]):
        bigram_freq[w1][w2] += 1

    return {
        w1: {w2: count / sum(next_dict.values()) for w2, count in next_dict.items()}
        for w1, next_dict in bigram_freq.items()
    }


def calculate_perplexity(sentence, bigram_model):
    words = sentence.split()
    if len(words) < 2:
        return 0

    perplexity = 1.0
    smoothing_value = 1e-2
    for w1, w2 in zip(words, words[1:]):
        prob = bigram_model.get(w1, {}).get(w2, smoothing_value)
        perplexity *= 1 / prob
    return math.pow(perplexity, 1 / len(words))


class Entity:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True

    def update(self):
        pass

    def draw(self):
        pass


class Bullet(Entity):
    def update(self):
        self.x += BULLET_SPEED
        if self.x > WINDOW_W:
            self.active = False

    def draw(self):
        pyxel.rect(self.x, self.y, 2, 2, 10)


class Token(Entity):
    def __init__(self, text, x, y):
        super().__init__(x, y)
        self.text = text

    def update(self):
        self.x -= TOKEN_SPEED
        if self.x < -30:
            self.active = False

    def draw(self):
        color = pyxel.COLOR_RED if self.text == "." else 7
        pyxel.text(self.x, self.y, self.text, color)


class App:
    def __init__(self):
        pyxel.init(WINDOW_W, WINDOW_H, title="Sentence Builder Shooter", fps=30)
        self.bigram_model = train_bigram_model(CORPUS)
        self.reset_game()
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        self.player_x = 20
        self.player_y = (WINDOW_H + UI_HEIGHT) // 2
        self.score = 0
        self.bullets = []
        self.tokens = []
        self.spawn_timer = 0
        self.generated_sentence = random.choice(HEAD_WORDS)
        self.is_game_over = False

    def spawn_token(self):
        for _ in range(random.randint(2, 3)):
            word = random.choice(FAKE_WORDS + ["</s>"] * (len(FAKE_WORDS) // 10))
            self.tokens.append(Token(word, WINDOW_W + 10, random.randint(UI_HEIGHT + 10, WINDOW_H - 10)))

    def update(self):
        if self.is_game_over:
            if pyxel.btnp(pyxel.KEY_R):
                self.reset_game()
            return

        self.update_player()
        self.update_bullets()
        self.update_tokens()
        self.check_collisions()

        if calculate_perplexity(self.generated_sentence, self.bigram_model) > 50:
            self.is_game_over = True

    def update_player(self):
        if pyxel.btn(pyxel.KEY_LEFT):
            self.player_x = max(self.player_x - PLAYER_SPEED, 0)
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.player_x = min(self.player_x + PLAYER_SPEED, WINDOW_W - 8)
        if pyxel.btn(pyxel.KEY_UP):
            self.player_y = max(self.player_y - PLAYER_SPEED, UI_HEIGHT)
        if pyxel.btn(pyxel.KEY_DOWN):
            self.player_y = min(self.player_y + PLAYER_SPEED, WINDOW_H - 8)
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.bullets.append(Bullet(self.player_x + 8, self.player_y + 4))

    def update_bullets(self):
        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.active:
                self.bullets.remove(bullet)

    def update_tokens(self):
        self.spawn_timer += 1
        if self.spawn_timer > TOKEN_SPAWN_INTERVAL:
            self.spawn_timer = 0
            self.spawn_token()
        for token in self.tokens[:]:
            token.update()
            if not token.active:
                self.tokens.remove(token)

    def check_collisions(self):
        for bullet in self.bullets:
            for token in self.tokens:
                if abs(bullet.x - token.x) < 6 and abs(bullet.y - token.y) < 6:
                    bullet.active = False
                    token.active = False
                    self.handle_token_hit(token)

    def handle_token_hit(self, token):
        if token.text == "</s>":
            self.generated_sentence = random.choice(HEAD_WORDS)
        else:
            self.score += 1
            self.generated_sentence += " " + token.text

    def draw(self):
        pyxel.cls(0)
        pyxel.rect(0, 0, WINDOW_W, UI_HEIGHT, 1)
        pyxel.text(5, 5, f"SCORE: {self.score}", 7)
        pyxel.text(5, 15, f"Sentence: {' '.join(self.generated_sentence.split()[-5:])}", 7)
        pyxel.text(5, 25, f"Perplexity: {calculate_perplexity(self.generated_sentence, self.bigram_model):.2f}", 7)
        pyxel.rect(self.player_x, self.player_y, 8, 8, 11)
        for bullet in self.bullets:
            bullet.draw()
        for token in self.tokens:
            token.draw()
        if self.is_game_over:
            draw_big_text(WINDOW_W // 2 - 30, WINDOW_H // 2 - 8, "GAME OVER", text_col=8, outline_col=0)
            pyxel.text(WINDOW_W // 2 - 40, WINDOW_H // 2 + 10, "Press R to Restart", pyxel.COLOR_WHITE)


def main():
    App()


if __name__ == "__main__":
    main()
