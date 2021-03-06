/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup cmpnodes
 */

#include "node_composite_util.hh"

/* ******************* Color Spill Suppression ********************************* */
static bNodeSocketTemplate cmp_node_color_spill_in[] = {
    {SOCK_RGBA, N_("Image"), 1.0f, 1.0f, 1.0f, 1.0f},
    {SOCK_FLOAT, N_("Fac"), 1.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f, PROP_FACTOR},
    {-1, ""},
};

static bNodeSocketTemplate cmp_node_color_spill_out[] = {
    {SOCK_RGBA, N_("Image")},
    {-1, ""},
};

static void node_composit_init_color_spill(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeColorspill *ncs = (NodeColorspill *)MEM_callocN(sizeof(NodeColorspill), "node colorspill");
  node->storage = ncs;
  node->custom1 = 2;    /* green channel */
  node->custom2 = 0;    /* simple limit algorithm */
  ncs->limchan = 0;     /* limit by red */
  ncs->limscale = 1.0f; /* limit scaling factor */
  ncs->unspill = 0;     /* do not use unspill */
}

void register_node_type_cmp_color_spill(void)
{
  static bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_COLOR_SPILL, "Color Spill", NODE_CLASS_MATTE, 0);
  node_type_socket_templates(&ntype, cmp_node_color_spill_in, cmp_node_color_spill_out);
  node_type_init(&ntype, node_composit_init_color_spill);
  node_type_storage(
      &ntype, "NodeColorspill", node_free_standard_storage, node_copy_standard_storage);

  nodeRegisterType(&ntype);
}
