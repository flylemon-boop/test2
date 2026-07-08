import torch
from einops import rearrange


def index_first_axis(x: torch.Tensor, indices: torch.Tensor) -> torch.Tensor:
    return x.index_select(0, indices)


def unpad_input(hidden_states: torch.Tensor, attention_mask: torch.Tensor):
    batch_size, seqlen = attention_mask.shape
    flat_mask = attention_mask.reshape(-1).to(dtype=torch.bool)
    indices = torch.nonzero(flat_mask, as_tuple=False).flatten()
    flat_hidden = hidden_states.reshape(batch_size * seqlen, *hidden_states.shape[2:])
    unpadded = flat_hidden.index_select(0, indices)
    seqlens = attention_mask.sum(dim=-1, dtype=torch.int32)
    cu_seqlens = torch.zeros(batch_size + 1, dtype=torch.int32, device=attention_mask.device)
    cu_seqlens[1:] = torch.cumsum(seqlens, dim=0)
    max_seqlen = int(seqlens.max().item()) if batch_size else 0
    return unpadded, indices, cu_seqlens, max_seqlen


def pad_input(hidden_states: torch.Tensor, indices: torch.Tensor, batch: int, seqlen: int) -> torch.Tensor:
    flat_shape = (batch * seqlen, *hidden_states.shape[1:])
    flat = hidden_states.new_zeros(flat_shape)
    flat.index_copy_(0, indices, hidden_states)
    return flat.reshape(batch, seqlen, *hidden_states.shape[1:])
