import torch.nn as nn
import torch
from models.MyTransformer import MyTransformer
from torch.nn import Transformer as MyTransformer
from models.Embedding import PositionalEncoding, TokenEmbedding


class AttentionBlock(nn.Module):
    def __init__(self, src_vocab_size_list, tgt_vocab_size, n_dis,
                 d_model=20, nhead=4, num_encoder_layers=6,
                 num_decoder_layers=6, dim_feedforward=2048,
                 dropout=0.1):
        super(AttentionBlock, self).__init__()
        self.my_transformer = MyTransformer(d_model=d_model,
                                            nhead=nhead,
                                            num_encoder_layers=num_encoder_layers,
                                            num_decoder_layers=num_decoder_layers,
                                            dim_feedforward=dim_feedforward,
                                            dropout=dropout)
        self.pos_embedding = PositionalEncoding(d_model=d_model, dropout=dropout)
        self.src_token_embedding_list = [TokenEmbedding(src_vocab_size, d_model) for src_vocab_size in src_vocab_size_list]
        self._reset_parameters()

    def forward(self, src_list=None, tgt=None, src_mask=None,
                tgt_mask=None, memory_mask=None, src_key_padding_mask=None,
                tgt_key_padding_mask=None, memory_key_padding_mask=None):
        """

        :param src: Encoder的输入 [src_len,batch_size]
        :param tgt: Decoder的输入 [tgt_len,batch_size]
        :param src_key_padding_mask: 用来Mask掉Encoder中不同序列的padding部分,[batch_size, src_len]
        :param tgt_key_padding_mask: 用来Mask掉Decoder中不同序列的padding部分 [batch_size, tgt_len]
        :param memory_key_padding_mask: 用来Mask掉Encoder输出的memory中不同序列的padding部分 [batch_size, src_len]
        :return:
        """
        src_embed_list = [self.src_token_embedding_list[i](src) for i, src in enumerate(src_list)]  # [src_len, batch_size, embed_dim]
        src_embed_list = [self.pos_embedding(src_embed) for src_embed in src_embed_list]  # [src_len, batch_size, embed_dim]
        tgt_embed = self.src_token_embedding_list[0](tgt)  # [tgt_len, batch_size, embed_dim]
        tgt_embed = self.pos_embedding(tgt_embed)  # [tgt_len, batch_size, embed_dim]
        src_embed = torch.cat(src_embed_list, dim=0)
        src_key_padding_mask = torch.cat(src_key_padding_mask, dim=1)
        outs = self.my_transformer(src=src_embed, tgt=tgt_embed, src_mask=src_mask,
                                   tgt_mask=tgt_mask, memory_mask=memory_mask,
                                   src_key_padding_mask=src_key_padding_mask,
                                   tgt_key_padding_mask=tgt_key_padding_mask,
                                   memory_key_padding_mask=memory_key_padding_mask)
        # [tgt_len,batch_size,embed_dim]
        outs = outs.squeeze(0)
        outs[outs.isnan()] = 0
        return outs #[batch_size,embed_dim]

    def encoder(self, src):
        src_embed = self.src_token_embedding(src)  # [src_len, batch_size, embed_dim]
        src_embed = self.pos_embedding(src_embed)  # [src_len, batch_size, embed_dim]
        memory = self.my_transformer.encoder(src_embed)
        return memory

    def decoder(self, tgt, memory):
        tgt_embed = self.tgt_token_embedding(tgt)  # [tgt_len, batch_size, embed_dim]
        tgt_embed = self.pos_embedding(tgt_embed)  # [tgt_len, batch_size, embed_dim]
        outs = self.my_transformer.decoder(tgt_embed, memory=memory)  # [tgt_len,batch_size,embed_dim]
        return outs

    def _reset_parameters(self):
        r"""Initiate parameters in the transformer model."""
        """
        初始化
        """
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
