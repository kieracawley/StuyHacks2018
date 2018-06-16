from keras.models import Sequential, load_model
from keras.layers import LSTM, Dense, Embedding
from keras.preprocessing.sequence import pad_sequences
from keras.callbacks import LambdaCallback, ModelCheckpoint
import pickle as pkl
import numpy as np
import sys

from keras.backend import manual_variable_initialization
manual_variable_initialization(False)

from keras import backend as K
print(K.tensorflow_backend._get_available_gpus())

with open('training_data.txt') as f:
    data = f.read()
    corpus = data.split()

a = set(corpus)


start_symbol, end_symbol = '<s>', '</s>'
a.update({start_symbol, end_symbol})

char2ind = {i: c+1 for c, i in enumerate(a)}
ind2char = {v: k for k, v in char2ind.items()}

tunes = data.split('\n\n')
tunes = [[char2ind[c] for c in [start_symbol] + t.split() + [end_symbol]] for t in tunes]
tunes.sort(key=lambda x: len(x), reverse=True)
ntunes = len(tunes)

tune_lens = np.array([len(t) for t in tunes])
max_len = max(tune_lens)
max_len = 200

print('n tunes:', ntunes)
print('min, max length', min(tune_lens), max(tune_lens))



NUM_CLASSES = len(a)
BATCH_SIZE = 32

with open("char2ind.pkl", 'wb+') as f:
    pkl.dump(char2ind, f)

with open("ind2char.pkl", 'wb+') as f:
    pkl.dump(ind2char, f)




model = Sequential()
model.add(Embedding(NUM_CLASSES+1, NUM_CLASSES, mask_zero=True))
model.add(LSTM(256))
model.add(Dense(NUM_CLASSES+1, activation='softmax'))
model.compile(loss='categorical_crossentropy', optimizer='adam')
from DataIterator import DataIterator
generator = DataIterator(tunes, tune_lens, max_len, BATCH_SIZE, NUM_CLASSES)


def sample(preds, temperature=1.0):
    # helper function to sample an index from a probability array
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)


def on_epoch_end(epoch, logs):
    # Function invoked at end of each epoch. Prints generated text.
    print()
    print('----- Generating text after Epoch: %d' % epoch)

    for diversity in [0.2, 0.5, 1.0, 1.2]:
        print('----- diversity:', diversity)

        generated = start_symbol
        print('----- Generating with seed: "' + generated + '"')
        sys.stdout.write(generated)
        count = 0
        while generated.split()[-1] != end_symbol and count < 100:
            x_pred = pad_sequences([[char2ind[i] for i in generated.split()]], max_len, padding='post', truncating='pre')

            preds = model.predict(x_pred, verbose=0)[0]
            next_index = sample(preds, diversity)
            try:
                next_char = ind2char[next_index]
            except:
                next_char = ""

            generated += ' ' + next_char

            sys.stdout.write(' ' + next_char)
            sys.stdout.flush()
            count+=1
        print()

print_callback = LambdaCallback(on_epoch_end=on_epoch_end)


# model = load_model(r"C:\Users\Jason\PyCharmProjects\ABCRNN\saved_models\04-1.5125.hdf5")
#
# for i in range(10):
#     on_epoch_end(i, None)


callback = ModelCheckpoint(r"C:\Users\Jason\PyCharmProjects\ABCRNN\saved_models\{epoch:02d}-{loss:.4f}.h5")
model.summary()
model.fit_generator(generator, len(corpus)//BATCH_SIZE//1000, epochs=120, verbose=1, callbacks=[callback, print_callback])

# def test(model):
#     # Function invoked at end of each epoch. Prints generated text.
#     print()
#     print('----- Generating text after Epoch: %d')
#
#     start_index = random.randint(0, len(corpus) - LOOK_BACK - 1)
#     for diversity in [0.2, 0.5, 1.0, 1.2]:
#         print('----- diversity:', diversity)
#
#         generated = ''
#         sentence = corpus[start_index: start_index + LOOK_BACK]
#         generated += sentence
#         print('----- Generating with seed: "' + sentence + '"')
#         sys.stdout.write(generated)
#
#         for i in range(400):
#             x_pred = np.zeros((1, LOOK_BACK, NUM_CLASSES))
#             for t, char in enumerate(sentence):
#                 x_pred[0, t, char2ind[char]] = 1.
#
#             preds = model.predict(x_pred, verbose=0)[0]
#             next_index = sample(preds, diversity)
#             next_char = ind2char[next_index]
#
#             generated += next_char
#             sentence = sentence[1:] + next_char
#
#             sys.stdout.write(next_char)
#             sys.stdout.flush()
#         print()
#
# from keras.models import load_model
# model = load_model(r"C:\Users\Jason\PyCharmProjects\ABCRNN\saved_models\02-1.3303.hdf5")
#
# test(model, 1)