from geometry import Square, PlacedSquare
from pkga import Specimen, Gene
import random
import numpy as np

class OrderedSquare(Square):
    def __init__(self, width, height, order, flip=False):
        self.order = order
        
        if flip:
            Square.__init__(self, width, height)
        else:
            Square.__init__(self, height, width)
    
    def __repr__(self):
        return f"{Square.__repr__(self)} order: {self.order}"

    def place(self, parent_square, placed_squares):
        placed_squares = sorted(placed_squares, key=lambda x:x.y_pos + x.height)

        for square in placed_squares:
            p = square.lower_right[1]
            t = p + self.height
            r = square.lower_right[0]
            l = r - self.width

            on_this_square = list(filter(lambda x:x.is_within(p,t) and x!=square and x.x_pos + x.width < l, placed_squares))
            if len(on_this_square) == 0:
                x_p = 0
            else:
                rightmost = max(on_this_square, key=lambda x:x.lower_right[0])
                x_p = rightmost.lower_right[0]

            sqr = PlacedSquare(x_p, square.lower_right[1], self.width, self.height)

            parent_overlap = sqr.check_overlap(parent_square)
            if parent_overlap != sqr.area:
                continue
            
            overlap_detected = False
            for compared in placed_squares:
                if compared == square:
                    continue
                
                overlap = sqr.check_overlap(compared)
                if overlap != 0:
                    overlap_detected = True

            if overlap_detected:
                continue
            return sqr

class PermutationSquareInitializer:
    def __init__(self, permutation_count, permutation_bits):
        self.permutation_count = permutation_count
        self.permutation_bits = permutation_bits

        self.format = '{:0' + str(self.permutation_bits) + 'b}'

    def get_random_permutation(self):
        l = list(range(self.permutation_count))
        random.shuffle(l)
        return l

    def get_random_flip_vector(self):
        return np.random.choice([True, False], size=self.permutation_count)

    def generate_string(self, permutation, flip):
        k = self.permutation_bits + 1
        l = permutation
        specimen_arr = [None] * (self.permutation_count * k)

        w_index = 0
        for i in range(len(l)):
            bitnum = [bool(int(x)) for x in self.format.format(l[i])]
            for bit in bitnum:
                specimen_arr[w_index] = bit
                w_index += 1

            specimen_arr[w_index] = flip[i]
            w_index +=1

        return specimen_arr

    def create_specimen(self, template):
        p = self.get_random_permutation()
        f = self.get_random_flip_vector()
        specimen_arr = self.generate_string(p,f)

        return Specimen(Gene(specimen_arr), template)

class PermutationWithFlipMutator:
    def __init__(self, mutation_rate, bin_size, bin_amount):
        self.pmut = mutation_rate
        self.bin_size = bin_size
        self.bin_amount = bin_amount

    def mutate_flip_bytes(self, specimen):
        g = specimen.genome.bit_string
        for i in range(self.bin_size -1, len(g), self.bin_size):
            if random.random() < self.pmut:
                g[i] = not g[i]

    def mutate_permutation_bins(self, specimen):
        g = specimen.genome.bit_string
        if random.random() > self.pmut:
            return

        a = random.randint(0, self.bin_amount)
        b = random.randint(0, self.bin_amount)

        a_bin = g[a:a+self.bin_size]
        g[a:a+self.bin_size] = g[b:b+self.bin_size]
        g[b:b+self.bin_size] = a_bin

        


    def mutate(self, specimen, generation):
        self.mutate_flip_bytes(specimen)


class SQMutator:
    def __init__(self, default_mutation_rate):
        self.default_mutation_rate = default_mutation_rate
    def mutate(self, specimen, generation):
        mutation_rate = self.default_mutation_rate
        specimen.mutate(mutation_rate)

class SquareFittingEvaluator:
    def __init__(self, parent_square, fit_squares):
        self.fit_squares = fit_squares
        self.parent_square = parent_square

    def map_data(self, decoded_specimen):
        placed_squares = []
        ind = 0 
        d = decoded_specimen.decode()
        for key, value in d.items():
            matching_square = self.fit_squares[value["sqr_id"]]
            placed = OrderedSquare(matching_square.width, matching_square.height, ind, value["flip"])
            placed_squares.append(placed)
            ind += 1
        return placed_squares

    def place_rectangles(self, rectangles):
        top_boundary = PlacedSquare(0,0, self.parent_square.width, 0)
        placed_rects = [top_boundary]

        for rect in sorted(rectangles, key=lambda r:r.order):
            placed = rect.place(self.parent_square, placed_rects)

            if placed:
                placed_rects.append(placed)

        return placed_rects[1:]

    def calc_fitness(self, placed_rectangles):
        areas = map(lambda x: x.area, placed_rectangles)
        return pow(sum(areas),1)

    def evaluate(self, out, generation):
        rectangles = self.map_data(out)
        placed_rects = self.place_rectangles(rectangles)

        return self.calc_fitness(placed_rects)