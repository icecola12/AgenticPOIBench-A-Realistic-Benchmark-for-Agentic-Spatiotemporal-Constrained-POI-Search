"""
输入：B0FFGSY72R
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近3km约束：调用 maps_around_search(location="115.72814,37.531239", radius="3000", keywords="诊所")，验证返回的pois列表中包含 target_poi_id。
2) POI类型约束（门诊/诊所）：对 target_poi_id 调用 maps_search_detail(id="B0FFGSY72R") 获取名称与地址信息；并再次确认其来自步骤1以"诊所"为关键词的周边搜索结果（等价于被检索系统归类为诊所/门诊）。
3) 出发地->诊所驾车时间≤6分钟：从步骤2的 location 取诊所坐标，调用 maps_driving_by_coordinates(origin="115.72814,37.531239", destination=诊所坐标)，取 total_duration_seconds/60，验证 ≤6。
4) 诊所->枣强火车站驾车时间≤6分钟：先调用 maps_text_search(keywords="枣强火车站", city="衡水市", citylimit="true")，选取pois中“枣强站”(id="B013E002S4")；再调用 maps_search_detail(id="B013E002S4") 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 火车站坐标；最后调用 maps_driving_by_coordinates(origin=诊所坐标, destination=火车站坐标)，取 total_duration_seconds/60，验证 ≤6。
"""
import sys
import os
from typing import List, Dict

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_distance,
    maps_driving_by_coordinates ,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = "B0FFGSY72R",
    user_location: str = "115.72814,37.531239",
    around_search_radius: str = "3000",
    around_search_keywords: str = "诊所",
    max_user_to_clinic_driving_minutes: int = 6,
    station_keywords: str = "枣强火车站",
    station_city: str = "衡水市",
    station_citylimit: str = "true",
    station_poi_id: str = "B013E002S4",
    max_clinic_to_station_driving_minutes: int = 6
) -> bool:
    """
    验证POI ID是否符合给定的验证条件

    验证步骤：
    1) 附近3km约束：验证POI是否在用户附近3km内的诊所列表中
    2) POI类型约束：验证POI是否来自诊所关键词的搜索结果
    3) 出发地->诊所驾车时间≤6分钟：验证从用户位置到诊所的驾车时间
    4) 诊所->枣强火车站驾车时间≤6分钟：验证从诊所到火车站的驾车时间

    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        max_user_to_clinic_driving_minutes: 用户到诊所的最大驾车时间（分钟）
        station_keywords: 火车站搜索关键词
        station_city: 火车站所在城市
        station_citylimit: 火车站搜索城市限制
        station_poi_id: 火车站POI ID
        max_clinic_to_station_driving_minutes: 诊所到火车站的最大驾车时间（分钟）

    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 4

    # 实际用于后续计算的POI坐标，从POI详情中获取
    actual_poi_location = None

    # 验证步骤1: 附近3km约束验证
    print("验证步骤1: 附近3km约束验证")
    print(f"调用 maps_around_search(location=\"{user_location}\", radius=\"{around_search_radius}\", keywords=\"{around_search_keywords}\")")
    around_result = maps_around_search(
        location=user_location,
        radius=around_search_radius,
        keywords=around_search_keywords
    )

    if around_result.error:
        print(f"周边搜索失败: {around_result.error}")
        print("验证步骤1: 未通过")
    else:
        poi_found = False
        if around_result.pois:
            for poi in around_result.pois:
                if poi.id == target_poi_id:
                    poi_found = True
                    break

        if poi_found:
            print(f"验证步骤1: 通过 - 在周边搜索结果中找到目标POI ID: {target_poi_id}")
            passed_count += 1
        else:
            print(f"验证步骤1: 未通过 - 在周边搜索结果中未找到目标POI ID: {target_poi_id}")

    # 验证步骤2: POI类型约束验证
    print("\n验证步骤2: POI类型约束验证")
    print(f"调用 maps_search_detail(id=\"{target_poi_id}\")")
    detail_result = maps_search_detail(id=target_poi_id)

    if detail_result.error:
        print(f"POI详情查询失败: {detail_result.error}")
        print("验证步骤2: 未通过")
    else:
        # 获取名称信息
        poi_name = detail_result.name if detail_result.name else ""
        print(f"POI名称: {poi_name}")

        # 检查是否包含诊所相关关键词（步骤1已经验证了来自诊所搜索，所以这里主要确认名称合理性）
        name_contains_clinic_keywords = any(keyword in poi_name for keyword in ["诊所", "门诊", "医院", "医疗", "卫生"])

        if name_contains_clinic_keywords:
            print(f"验证步骤2: 通过 - POI名称 {poi_name} 符合诊所/门诊类型")
            passed_count += 1
        else:
            print(f"验证步骤2: 未通过 - POI名称 {poi_name} 不符合诊所/门诊类型")

        # 更新POI坐标
        if detail_result.location:
            actual_poi_location = detail_result.location
            print(f"获取到POI坐标: {actual_poi_location}")

    # 验证步骤3: 出发地->诊所驾车时间验证
    print("\n验证步骤3: 出发地->诊所驾车时间验证")
    if not actual_poi_location:
        print("验证步骤3: 未通过 - 无法获取POI坐标，无法规划驾车路线")
    else:
        print(f"调用 maps_driving_by_coordinates(origin=\"{user_location}\", destination=\"{actual_poi_location}\")")
        driving_result = maps_driving_by_coordinates(
            origin=user_location,
            destination=actual_poi_location
        )

        if driving_result.error:
            print(f"驾车路线规划失败: {driving_result.error}")
            print("验证步骤3: 未通过")
        else:
            if driving_result.total_duration_seconds is not None:
                duration_minutes = driving_result.total_duration_seconds / 60
                if duration_minutes <= max_user_to_clinic_driving_minutes:
                    print(f"验证步骤3: 通过 - 驾车时间 {duration_minutes:.1f}分钟 <= {max_user_to_clinic_driving_minutes}分钟")
                    passed_count += 1
                else:
                    print(f"验证步骤3: 未通过 - 驾车时间 {duration_minutes:.1f}分钟 > {max_user_to_clinic_driving_minutes}分钟")
            else:
                print("验证步骤3: 未通过 - 无法获取驾车时间")

    # 验证步骤4: 诊所->枣强火车站驾车时间验证
    print("\n验证步骤4: 诊所->枣强火车站驾车时间验证")
    if not actual_poi_location:
        print("验证步骤4: 未通过 - 无法获取POI坐标，无法规划驾车路线")
    else:
        # 步骤4a: 获取枣强火车站坐标
        print(f"调用 maps_text_search(keywords=\"{station_keywords}\", city=\"{station_city}\", citylimit=\"{station_citylimit}\")")
        station_search_result = maps_text_search(
            keywords=station_keywords,
            city=station_city,
            citylimit=station_citylimit
        )

        station_location = None
        if station_search_result.error:
            print(f"文本搜索失败: {station_search_result.error}")
            print("验证步骤4: 未通过")
        else:
            station_id = None
            if station_search_result.pois:
                # 查找期望的车站POI ID
                for poi in station_search_result.pois:
                    if poi.id == station_poi_id:
                        station_id = poi.id
                        break

                # 如果没找到期望的ID，使用第一个结果
                if not station_id and len(station_search_result.pois) > 0:
                    station_id = station_search_result.pois[0].id
                    print(f"未找到期望的车站ID {station_poi_id}，使用搜索结果中的第一个POI ID: {station_id}")

            if station_id:
                print(f"获取到车站POI ID: {station_id}")
                print(f"调用 maps_search_detail(id=\"{station_id}\")")
                station_detail_result = maps_search_detail(id=station_id)

                if station_detail_result.error:
                    print(f"车站详情查询失败: {station_detail_result.error}")
                    print("验证步骤4: 未通过")
                else:
                    if station_detail_result.location:
                        station_location = station_detail_result.location
                        print(f"获取到车站坐标: {station_location}")

                        # 步骤4b: 计算驾车时间
                        print(f"调用 maps_driving_by_coordinates(origin=\"{actual_poi_location}\", destination=\"{station_location}\")")
                        station_driving_result = maps_driving_by_coordinates(
                            origin=actual_poi_location,
                            destination=station_location
                        )

                        if station_driving_result.error:
                            print(f"驾车路线规划失败: {station_driving_result.error}")
                            print("验证步骤4: 未通过")
                        else:
                            if station_driving_result.total_duration_seconds is not None:
                                station_duration_minutes = station_driving_result.total_duration_seconds / 60
                                if station_duration_minutes <= max_clinic_to_station_driving_minutes:
                                    print(f"验证步骤4: 通过 - 驾车时间 {station_duration_minutes:.1f}分钟 <= {max_clinic_to_station_driving_minutes}分钟")
                                    passed_count += 1
                                else:
                                    print(f"验证步骤4: 未通过 - 驾车时间 {station_duration_minutes:.1f}分钟 > {max_clinic_to_station_driving_minutes}分钟")
                            else:
                                print("验证步骤4: 未通过 - 无法获取驾车时间")
                    else:
                        print("验证步骤4: 未通过 - 无法获取车站坐标")
            else:
                print("验证步骤4: 未通过 - 未找到车站POI")

    # 输出最终结果
    print(f"\n验证完成: 通过 {passed_count}/{total_count} 项验证")
    if passed_count == total_count:
        print("最终验证结果: True (完全满足所有验证条件)")
        return True
    else:
        print("最终验证结果: False (部分满足或不满足验证条件)")
        return False


def main():
    result = verify_poi()
    print(f"\n函数返回值: {result}")


if __name__ == "__main__":
    main()
