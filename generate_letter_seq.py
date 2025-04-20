import random as rd
import string

def generate_letter_seq(n, x):
    """
    Generates a 70-character sequence with targets for an N-back task.
    
    Args:
      n (int): N-back level (e.g., 1, 2, or 3).
      x (int): Number of targets to include in the sequence.
      
    Returns:
      list: Generated sequence with targets.
      list: Positions of the targets within the sequence.
    """
    m = 70  # Sequence length
    min_dist = n + 2  
    max_dist = 7  

    # Generate initial sequence
    seq = [rd.choice(string.ascii_uppercase)]
    while len(seq) < m:
        letter = rd.choice(string.ascii_uppercase)
        if letter != seq[-1]:
            seq.append(letter)
    
    # Generate unique target positions with minimum spacing
    pos_list = set()
    while len(pos_list) < x:
        pos = rd.randint(min_dist, m - 1)
        if all(abs(pos - p) >= min_dist for p in pos_list):
            pos_list.add(pos)
    pos_list = sorted(pos_list)
    
    # Insert targets according to n-back rule
    for j in pos_list:
        if j - n >= 0:
            seq[j] = seq[j - n]
    
    return seq, pos_list

if __name__ == "__main__":
    n_back_level = 2  
    num_targets = 10  
    sequence, targets = generate_letter_seq(n_back_level, num_targets)
    print("Generated Sequence:", "".join(sequence))
    print("Target Positions:", targets)
