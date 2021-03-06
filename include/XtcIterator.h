#ifndef PSANA_TEST_XTCITERATOR
#define PSANA_TEST_XTCITERATOR

#include <stdint.h>

// copied from pdsdata

/*
** ++
**  Package:
**	OdfContainer
**
**  Abstract:
**      This class allows iteration over a collection of "odfInXtcs".
**      An "event" generated from DataFlow consists of data described
**      by a collection of "odfInXtcs". Therefore, this class is 
**      instrumental in the navigation of an event's data. The set of 
**      "odfInXtcs" is determined by passing (typically to the constructor)
**      a root "odfInXtc" which describes the collection of "odfInXtcs"
**      to process. This root, for example is provided by an event's
**      datagram. As this is an Abstract-Base-Class, it is expected that an 
**      application will subclass from this class, providing an implementation
**      of the "process" method. This method will be called back for each
**      "odfInXtc" in the collection. Note that the "odfInXtc" to process
**      is passed as an argument. If the "process" method wishes to abort
**      the iteration a zero (0) value is returned. The iteration is initiated
**      by calling the "iterate" member function.
**      
**  Author:
**      Michael Huffer, SLAC, (415) 926-4269
**
**  Creation Date:
**	000 - October 11,1998
**
**  Revision History:
**	Modified to take a diagnose flag for more output - David
**
** --
*/

namespace Pds {
  class Xtc;
};

namespace psana_test {


class XtcIterator
  {
  public:
    XtcIterator(Pds::Xtc* root, bool diagnose, uint32_t maxXtcExtent);
    XtcIterator() {}
   virtual ~XtcIterator() {}
  public:
    virtual int process(Pds::Xtc* xtc) = 0;
  public:
    void            iterate();
    void            iterate(Pds::Xtc*);
    const Pds::Xtc* root()              const;
  private:
     Pds::Xtc* _root; // Collection to process in the absence of an argument...
     bool _diagnose;
     uint32_t _maxXtcExtent;
  };

}

using namespace psana_test;

/*
** ++
**
**    This constructor takes an argument the "Xtc" which defines the
**    collection to iterate over.
**
**
** --
*/

inline XtcIterator::XtcIterator(Pds::Xtc* root, bool diagnose, uint32_t maxXtcExtent) :
                   _root(root), _diagnose(diagnose), _maxXtcExtent(maxXtcExtent)
  {
  } 

/*
** ++
**
**    This function will return the collection specified by the constructor.
**
** --
*/

inline const Pds::Xtc* XtcIterator::root() const
  {
  return _root;
  } 

/*
** ++
**
**    This function will commence iteration over the collection specified
**    by the constructor. 
**
** --
*/

inline void XtcIterator::iterate() 
  {
  iterate(_root);
  } 

#endif
