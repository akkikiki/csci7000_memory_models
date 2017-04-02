from dynet import *
import time
import random

LAYERS = 1
INPUT_DIM = 5 #50  #256
HIDDEN_DIM = 5 # 50  #1024
VOCAB_SIZE = 0

from collections import defaultdict
from itertools import count
import sys
import util


class RNNLanguageModel:
    def __init__(self, model, LAYERS, INPUT_DIM, HIDDEN_DIM, VOCAB_SIZE, builder=SimpleRNNBuilder):
        self.builder = builder(LAYERS, INPUT_DIM, HIDDEN_DIM, model)

        self.lookup = model.add_lookup_parameters((VOCAB_SIZE, INPUT_DIM))
        self.R = model.add_parameters((VOCAB_SIZE, HIDDEN_DIM))
        self.bias = model.add_parameters((VOCAB_SIZE))
        #print(dir(model))
        #print(dir(self.builder))
        #print(model.thisptr.parameters_list())
        #print(model.pl_full())

    def save_to_disk(self, filename):
        model.save(filename, [self.builder, self.lookup, self.R, self.bias])

    def load_from_disk(self, filename):
        (self.builder, self.lookup, self.R, self.bias) = model.load(filename)
        
    def build_lm_graph(self, sent):
        renew_cg()
        init_state = self.builder.initial_state()

        R = parameter(self.R)
        bias = parameter(self.bias)
        errs = [] # will hold expressions
        es=[]
        state = init_state
        for (cw,nw) in zip(sent,sent[1:]):
            # assume word is already a word-id
            x_t = lookup(self.lookup, int(cw))
            state = state.add_input(x_t)
            y_t = state.output()
            r_t = bias + (R * y_t)
            #print(state.h()[0])
            #print(state.s()[0])
           # print(state.s())
            #print(dir(state))
            #print(state.s()[0].value())
            #print(self.R.as_array())
            #print(self.bias.as_array())
            err = pickneglogsoftmax(r_t, int(nw))
            errs.append(err)
        nerr = esum(errs)
        return nerr
    
    def predict_next_word(self, sentence):
        renew_cg()
        init_state = self.builder.initial_state()
        R = parameter(self.R)
        bias = parameter(self.bias)
        state = init_state
        for cw in sentence:
            # assume word is already a word-id
            x_t = lookup(self.lookup, int(cw))
            state = state.add_input(x_t)
        y_t = state.output()
        r_t = bias + (R * y_t)
        prob = softmax(r_t)
        return prob
    
    def sample(self, first=1, nchars=0, stop=-1):
        res = [first]
        renew_cg()
        state = self.builder.initial_state()

        R = parameter(self.R)
        bias = parameter(self.bias)
        cw = first
        while True:
            x_t = lookup(self.lookup, cw)
            state = state.add_input(x_t)
            y_t = state.output()
            r_t = bias + (R * y_t)
            ydist = softmax(r_t)
            dist = ydist.vec_value()
            rnd = random.random()
            i = 0
            for i,p in enumerate(dist):
                rnd -= p
                if rnd <= 0: break
            res.append(i)
            cw = i
            if cw == stop: break
            if nchars and len(res) > nchars: break
            #break # for visualization purpose
        return res

if __name__ == '__main__':
    train = util.CharsCorpusReader(sys.argv[1],begin="<s>")
    vocab = util.Vocab.from_corpus(train)
    
    VOCAB_SIZE = vocab.size()

    model = Model()
    sgd = SimpleSGDTrainer(model)

    lm = RNNLanguageModel(model, LAYERS, INPUT_DIM, HIDDEN_DIM, VOCAB_SIZE, builder=SimpleRNNBuilder)
    f_out = open("loss_simplernn_rnnlm.txt", "w")
    #lm = RNNLanguageModel(model, LAYERS, INPUT_DIM, HIDDEN_DIM, VOCAB_SIZE, builder=LSTMBuilder)
    #f_out = open("loss_lstm_rnnlm.txt", "w")


    train = list(train)

    chars = loss = 0.0
    for ITER in range(400):
    #for ITER in range(1):
        random.shuffle(train)
        for i,sent in enumerate(train):
            _start = time.time()
            if i % 50 == 0:
                sgd.status()
                if chars > 0: print(loss / chars,)
                for _ in range(1):
                    samp = lm.sample(first=vocab.w2i["<s>"],stop=vocab.w2i["\n"])
                    print("".join([vocab.i2w[c] for c in samp]).strip())
                loss = 0.0
                chars = 0.0
                
            chars += len(sent)-1
            isent = [vocab.w2i[w] for w in sent]
            errs = lm.build_lm_graph(isent)
            loss += errs.scalar_value()
            errs.backward()
            sgd.update(1.0)

            #print "TM:",(time.time() - _start)/len(sent)
        print("ITER=%i, loss=%.4f" % (ITER,loss))
        #f_out.write("%.4f\n" % (ITER, loss))
        #f_out.write("%.4f\t" % (loss))
        sgd.status()
        sgd.update_epoch(1.0)

    #print_graphviz(expression_names={ lm.R: "R",
    #                                  lm.bias: "bias",
    #                                  lm.lookup: "lookup"
    #                                },
    #                )
