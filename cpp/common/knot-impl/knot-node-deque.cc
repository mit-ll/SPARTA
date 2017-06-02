//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation of KnotNodeDeque, Iterators, etc.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Jul 2012   omd            Original Version
//*****************************************************************

#include "knot-node-deque.h"

#include <algorithm>
#include <iostream>

KnotNodeDeque::KnotNodeDeque() {
}

// Can't just copy the deque or we'd have two deque's with pointers to the same
// nodes and that would cause memory issues. Need to construct new KnotNode
// instances too.
KnotNodeDeque::KnotNodeDeque(const KnotNodeDeque& other) {
  NodeDeque::const_iterator i;
  for (i = other.deque_.begin(); i != other.deque_.end(); ++i) {
    deque_.push_back(new KnotNode(**i));
  }
}


KnotNodeDeque::~KnotNodeDeque() {
  NodeDeque::iterator i;
  for (i = deque_.begin(); i != deque_.end(); ++i) {
    delete *i;
  }
}

void KnotNodeDeque::Append(const Strand* strand) {
  KnotNode::SharedStrand shared_strand(strand);
  Append(shared_strand);
}

void KnotNodeDeque::Append(KnotNode::SharedStrand strand) {
  CHECK(strand.get() != NULL);
  KnotNode* node = new KnotNode(strand);
  deque_.push_back(node);
  if (deque_.size() > 1) {
    KnotNode* left_node = deque_.at(deque_.size() - 2);
    node->set_cum_char_count(
        left_node->cum_char_count() +
        node->strand()->Size());
  } else {
    node->set_cum_char_count(node->strand()->Size());
  }
}

KnotNodeDeque* KnotNodeDeque::GetSubDeque(
    int start_offset, int num_nodes, Strand* left_replace,
    Strand* right_replace) {
  DCHECK(start_offset + num_nodes <= GetNumStrands());
  KnotNodeDeque* new_deque = new KnotNodeDeque;
  if (left_replace != NULL) {
    new_deque->Append(left_replace);
    --num_nodes;
    ++start_offset;
  }
  if (right_replace != NULL) {
    --num_nodes;
  }
  DCHECK(num_nodes >= 0);

  if (num_nodes > 0) {
    NodeDeque::const_iterator i;
    NodeDeque::const_iterator starting_it = deque_.begin() + start_offset;
    NodeDeque::const_iterator ending_it = starting_it + num_nodes;
    for (i = starting_it; i != ending_it; ++i) {
      new_deque->Append((*i)->strand());
    }
  }

  if (right_replace != NULL) {
    new_deque->Append(right_replace);
  }

  return new_deque;
}

// Functor for use with lower_bound call below.
class CharCountComparison {
 public:
  bool operator()(const KnotNode* k1, const KnotNode* k2) const {
    return k1->cum_char_count() < k2->cum_char_count();
  }

  bool operator()(const KnotNode* node, int char_num) const {
    return node->cum_char_count() < char_num;
  }

  bool operator()(int char_num, const KnotNode* node) const {
    return char_num < node->cum_char_count();
  }
};

int KnotNodeDeque::StrandWithChar(size_t char_idx, int* offset) const {
  std::deque<KnotNode*>::const_iterator node_it;
  node_it = std::lower_bound(deque_.begin(), deque_.end(), char_idx + 1,
                             CharCountComparison());
  CHECK(node_it != deque_.end());
  *offset = char_idx - (*node_it)->cum_char_count() +
      (*node_it)->strand()->Size();
  int strand_idx = node_it - deque_.begin();
  DCHECK(*offset >= 0);
  DCHECK(*offset < (*node_it)->strand()->Size());
  return strand_idx;
}

size_t KnotNodeDeque::GetCharCount() const {
  if (deque_.size() == 0) {
    return 0;
  } else {
    return deque_.back()->cum_char_count();
  }
}

int KnotNodeDeque::LeftCountForStrand(int strand_idx) const {
  DCHECK(strand_idx >= 0);
  DCHECK(strand_idx < static_cast<int>(deque_.size()));

  const KnotNode* node = deque_.at(strand_idx);
  return node->cum_char_count() - node->strand()->Size();
}
