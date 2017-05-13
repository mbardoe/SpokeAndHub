from partizangame import PartizanGame
import networkx as nx
import networkx.algorithms.isomorphism as iso
import copy
import matplotlib.pyplot as plt

try:
    from tinydb import TinyDB, Query
except:
    try:
        import sqlite3
    except:
        pass


class RedBlueCherries(PartizanGame):
    """Creates an instance of a game of Red Blue Cherries. Red Blue Cherries
    is played by defining a graph where the nodes are either red or blue. One
    player is red the other is blue. A player may move by removing a node of
    smallest degree that is their color. The game is over when one player
    does not have a move. That player is the loser.

    Args:

        num_nodes (int):    How many nodes will be in the graph.

        edges (list):   A list of tuples that define the edges of the graph.

        piles (list):   A list of strings ('r' and 'b') that define
                the value of each node of the graph.

        filename (str):     The filename of the database file we use.

        Returns:

            RedBlueCherries object.

        """

    def __init__(self, num_nodes, edges, piles, filename="redbluecherries.db"):


        self.__filename__ = filename
        super(RedBlueCherries, self).__init__(**{'filename': self.__filename__})
        self.graph = nx.Graph()
        self.graph.add_nodes_from(range(num_nodes))
        self.graph.add_edges_from(edges)
        for i in range(num_nodes):
            self.graph.node[i]['piles'] = piles[i]


    def __repr__(self):
        """Creates a string to print out as a representation of the game.

        Returns:
            str: A string that describes the game.
        """
        return "".join([str(self.graph.degree()), "\n", str(self.get_piles())])

    def __db_repr__(self):
        """Creates the database representation of the game.

        Returns:
            str: A string that list the piles in increasing order.
        """
        ### what about super when you inherit from 2 classes?
        return str(nx.incidence_matrix(self.graph)) + str(self.get_piles())

    def get_piles(self):
        """Returns a list indicating the value of each node.

        Returns:
            list: A list of strings ('r' and 'b').

        """
        piles_dict = nx.nx.get_node_attributes(self.graph, 'piles')
        return [piles_dict[i] for i in range(self.graph.number_of_nodes())]

    def possible_moves(self):
        """Compute all other games that are possible moves from this position.

        Returns:
            A list of the games that are all the possible moves from the given
            game.
        """
        ## this needs to be tested
        moves = {'left': [], 'right': []}
        nodes = self.find_min_nodes()
        for node in nodes:
            g = self.copy()
            g.remove_node(node)
            if self.graph.node[node]['piles'] == 'r':
                moves['right'].append(g)
            else:
                moves['left'].append(g)
        return moves

    def copy(self):
        """This method returns a copy of the current game.

        Returns:
            RedBlueCherries object with the same attributes as the current one.
        """

        edges = copy.deepcopy(self.graph.edges())
        piles = copy.deepcopy(self.get_piles())
        nodes = int(self.graph.number_of_nodes())
        return RedBlueCherries(nodes, edges, piles)

    def sub_values_by_player(self):
        """This method prints out the values that can be found at various nodes
        that represent the possible moves from this position. This is helpful
        when trying to calculate a value of game.

        Returns:
            A print out of the nodes that can be possible moves and the value
            of the game if that move is taken.
        """
        moves = self.possible_moves()
        print('left:\n')
        for move in moves['left']:
            print(move + ' ' + move.value)
        print('right:\n')
        for move in moves['right']:
            print(move + ' ' + move.value)

    def sub_values_by_node(self):
        """Returns a dictionary of the which nodes are associated with which
        values of the corresponding subgame. Only minimal vertex nodes are part
        of the keys.

        Returns:
            (dict): The keys are the minimal degree nodes. The values are the
                    the values of the game formed by removing that node.
        """
        ans = {}
        nodes = self.find_min_nodes()
        for node in nodes:
            g = self.copy()
            g.remove_node(node)
            ans[node] = g.value
        return ans

    def remove_node(self, node):
        """Removes a node from the graph. The graph is also re-indexed.

         Args:
            node (int): The index of the node that needs to be removed.
        """
        self.graph.remove_node(node)
        self.__validate__()

    def __validate__(self):
        """Makes sure the graph is indexed from 0 to n-1. Where n is the number
         of nodes.
        """
        ## make sure that no piles are zero.
        ## this needs to be tested.
        self.__rename_names__()

    def __eq__(self, other):
        """ Determines if two redbluecherry games are equal.

        Args:
            other (RedBlueCherries object): Another Red Blue Cherries game.

        Returns:
            bool: True if the graphs are isomorphic and the labels are the same.
        """
        nm = iso.categorical_node_match('piles', 0)
        return nx.is_isomorphic(self.graph, other.graph, node_match=nm)

    @property
    def value(self):
        """Calculates the value of this game via a depth search
        of possible moves.


        :return: int that is the equivalent game.
        """
        result = self.lookup_value()
        if result is None:
            ## Here will calculate the base cases by hand
            if self.graph.number_of_nodes() == 1:
                if self.graph.node[0]['piles'] == 'r':
                    return -1
                else:
                    return 1
            ## Here we will use a breadth search
            else:
                result = self.__tree_search__()
            self.__record_value__(self.__db_repr__(), result)
        return result

    ##### Graph Algorithms #######

    def find_min_nodes(self):
        """Finds the nodes of minimal degree.

         Returns:
            list: A list of integers which are the indexes of nodes of minimal
                    degree.
        """

        degrees = self.graph.degree()
        min_degree = min(degrees.values())
        return [key for key in degrees.keys() if degrees[key] == min_degree]

    def degree(self):
        """ Returns the degrees of each node.

        Returns:
            dict: A dictionary index by node indexes and whose values are the
                degree of that node.
        """
        return self.graph.degree()


    def color_dictionary(self):
        """Returns a dictionary with two keys, 'right' and 'left'. Allows us to
        know which nodes are right nodes and which are left nodes.

        Returns:
            (dict):     A dictionary with keys 'left' and 'right'. The values
                        of this these keys are lists of integers.
        """
        ans = {'right': [], 'left': []}
        for n in xrange(len(self.graph.node)):
            if self.graph.node[n]['piles'] == 'r':
                ans['right'].append(n)
            else:
                ans['left'].append(n)
        return ans

    def __rename_names__(self):
        """Changes the labelling of the vertices so that they correspond to
        smaller number indicate a leaf with small pile numbers.
        """
        self.graph = nx.convert_node_labels_to_integers(self.graph)

    def show_graph(self):
        """For use with Sage Math Cloud. Allows the creation of a
        matplotlib.pyplot object that is shown.
        """
        #labels
        labels = self.sub_values_by_node()
        G = self.graph
        pos = nx.spring_layout(G)  # positions for all nodes
        pos_higher = {}
        y_off = .1  # offset on the y axis
        for k, v in pos.items():
            pos_higher[k] = (v[0], v[1] + y_off)
        nx.draw_networkx_labels(G, pos_higher, labels, font_color='k')
        # nodes
        colors = self.color_dictionary()
        nx.draw_networkx_nodes(G, pos,
                               nodelist=colors['right'],
                               node_color='r',
                               node_size=700,
                               alpha=0.8)
        nx.draw_networkx_nodes(G, pos,
                               nodelist=colors['left'],
                               node_color='b',
                               node_size=700,
                               alpha=0.8)
        #edges
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)

        plt.show()  # display


def main():
    x = RedBlueCherries(6, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)],
                        ['b', 'b', 'b', 'r', 'r', 'r'])
    #x.nim_value()
    print x.find_min_nodes()
    print x.value


if __name__ == '__main__':
    main()