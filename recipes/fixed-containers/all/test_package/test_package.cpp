#include "fixed_containers/fixed_vector.hpp"

using namespace fixed_containers;

int main(void) {
  constexpr auto v1 = []() {
    FixedVector<int, 11> v{};
    v.push_back(0);
    v.emplace_back(1);
    v.push_back(2);
    return v;
  }();
  static_assert(v1[0] == 0);
  static_assert(v1[1] == 1);
  static_assert(v1[2] == 2);
  static_assert(v1.size() == 3);
  static_assert(v1.capacity() == 11);

  return 0;
}
