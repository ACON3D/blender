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
 */
#pragma once

/** \file
 * \ingroup balembic
 */

#include "abc_reader_object.h"

namespace blender::io::alembic {

class AbcNurbsReader final : public AbcObjectReader {
  std::vector<std::pair<Alembic::AbcGeom::INuPatchSchema, Alembic::Abc::IObject>> m_schemas;

 public:
  AbcNurbsReader(const Alembic::Abc::IObject &object, ImportSettings &settings);

  bool valid() const override;

  bool accepts_object_type(const Alembic::AbcCoreAbstract::ObjectHeader &alembic_header,
                           const Object *const ob,
                           const char **err_str) const override;

  void readObjectData(Main *bmain, const Alembic::Abc::ISampleSelector &sample_sel) override;

 private:
  void getNurbsPatches(const Alembic::Abc::IObject &obj);
};

}  // namespace blender::io::alembic
