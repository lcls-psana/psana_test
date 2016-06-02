#include <stdio.h>
#include "psana_test/smldata.h"
#include <stdexcept>

#define __STDC_FORMAT_MACROS
#include "inttypes.h"

bool isSmallData(const Pds::TypeId &typeId) {
  return (typeId.id() == Pds::TypeId::Id_SmlDataProxy) or 
    (typeId.id() == Pds::TypeId::Id_SmlDataOrigDgramOffset);
}

void parseSmallData(FILE *fout, const Pds::TypeId &typeId, const char *payload) {
  int version = typeId.version();
  switch (typeId.id()) {
  case Pds::TypeId::Id_SmlDataOrigDgramOffset:
    switch (version) {
    case 1:
    case 32769:
      const Pds::SmlData::OrigDgramOffsetV1 * origDgramOffset = static_cast<const Pds::SmlData::OrigDgramOffsetV1 *>(static_cast<const void *>(payload));
      int64_t fileOffset = origDgramOffset->fileOffset();
      uint32_t extent = origDgramOffset->extent();
      fprintf(fout, " fileOffset=%" PRId64 " (=0x%8.8" PRIx64 ") extent=%" PRIu32 " (=0x%4.4" PRIx32 ")",
              fileOffset, fileOffset, extent, extent);
      return;
    }
    throw std::runtime_error("parseSmallData - OrigDgramOffsetV1 - unknown version");
  case Pds::TypeId::Id_SmlDataProxy:
    switch (version) {
    case 1:
    case 32769:
      const Pds::SmlData::ProxyV1 * smlDataProxy = static_cast<const Pds::SmlData::ProxyV1 *>(static_cast<const void *>(payload));
      int64_t fileOffset = smlDataProxy->fileOffset();
      uint32_t extent = smlDataProxy->extent();
      fprintf(fout, " fileOffset=%" PRId64 " (=0x%8.8" PRIx64 ") extent=%" PRIu32 " (=0x%4.4" PRIx32 ")",
              fileOffset, fileOffset, extent, extent);
      return;
    }
    throw std::runtime_error("parseSmallData - SmlDataProxy - unknown version");
  default:
    throw std::runtime_error("parseSmallData - unknown TypeId");
  }
}

