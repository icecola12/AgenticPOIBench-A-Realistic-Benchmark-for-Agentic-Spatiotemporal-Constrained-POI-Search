"""
输入：B0LRNZKOFJ
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束(2公里内)：用 maps_around_search，以用户坐标126.996134,46.631925为中心、radius=2000、keywords=自习室 搜索，验证返回pois中包含目标poi_id=B0LRNZKOFJ。
2) 步行时间不超过10分钟：用 maps_search_detail(B0LRNZKOFJ) 获取目标location=126.996875,46.627475；再用 maps_walking_by_coordinates(origin=126.996134,46.631925, destination=126.996875,46.627475) 得到 total_duration_seconds=466，验证466<=600。
3) 开车到绥化站不超过5分钟：用 maps_search_detail(B01C700HKI) 获取绥化站location=127.015969,46.645209；再用 maps_driving_by_coordinates(origin=126.996875,46.627475, destination=127.015969,46.645209) 得到 poi_id，再 maps_search_detail(id=poi_id) 得到 total_duration_seconds=258，验证258<=300。
4) 评分不低于3.0：用 maps_search_detail(B0LRNZKOFJ) 读取 biz_ext.rating=3.3，验证3.3>=3.0。
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
    target_poi_id: str = "B0LRNZKOFJ",
    user_location: str = "126.996134,46.631925",
    around_search_radius: str = "2000",
    around_search_keywords: str = "自习室",
    max_walking_duration_seconds: int = 600,
    poi_location: str = "126.996875,46.627475",
    station_poi_id: str = "B01C700HKI",
    station_location: str = "127.015969,46.645209",
    max_driving_duration_seconds: int = 300,
    min_rating: float = 3.0
) -> bool:
    """
    验证POI ID是否符合给定的验证条件

    验证步骤：
    1) 距离约束(2公里内)：验证目标POI是否在用户附近2公里内的自习室列表中
    2) 步行时间不超过10分钟：验证从用户位置到POI的步行时间<=10分钟
    3) 开车到绥化站不超过5分钟：验证从POI到绥化站的驾车时间<=5分钟
    4) 评分不低于3.0：验证POI评分>=3.0

    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        max_walking_duration_seconds: 最大步行时间（秒），10分钟=600秒
        poi_location: POI位置坐标（如果从详情中未获取到可通过此参数传入）
        station_poi_id: 绥化站POI ID
        station_location: 绥化站位置坐标（如果从详情中未获取到可通过此参数传入）
        max_driving_duration_seconds: 最大驾车时间（秒），5分钟=300秒
        min_rating: 最低评分要求

    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 4

    # 实际用于后续计算的POI坐标，从POI详情中获取
    actual_poi_location = poi_location

    # 验证步骤1: 距离约束(2公里内)验证
    print("验证步骤1: 距离约束(2公里内)验证")
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

    # 验证步骤2: 步行时间不超过10分钟验证
    print("\n验证步骤2: 步行时间不超过10分钟验证")
    print(f"调用 maps_search_detail(id=\"{target_poi_id}\")")
    detail_result = maps_search_detail(id=target_poi_id)

    if detail_result.error:
        print(f"POI详情查询失败: {detail_result.error}")
        print("验证步骤2: 未通过")
    else:
        # 更新POI location（如果从详情中获取到了）
        if detail_result.location:
            actual_poi_location = detail_result.location
            print(f"从POI详情获取到location: {actual_poi_location}")

        if not actual_poi_location:
            print("验证步骤2: 未通过 - 无法获取POI坐标，无法规划步行路线")
        else:
            print(f"调用 maps_walking_by_coordinates(origin=\"{user_location}\", destination=\"{actual_poi_location}\")")
            walking_result = maps_walking_by_coordinates(
                origin=user_location,
                destination=actual_poi_location
            )

            if walking_result.error:
                print(f"步行路线规划失败: {walking_result.error}")
                print("验证步骤2: 未通过")
            else:
                if walking_result.total_duration_seconds is not None:
                    duration = walking_result.total_duration_seconds
                    if duration <= max_walking_duration_seconds:
                        print(f"验证步骤2: 通过 - 步行时间 {duration}秒 <= {max_walking_duration_seconds}秒")
                        passed_count += 1
                    else:
                        print(f"验证步骤2: 未通过 - 步行时间 {duration}秒 > {max_walking_duration_seconds}秒")
                else:
                    print("验证步骤2: 未通过 - 无法获取步行时间")

    # 验证步骤3: 开车到绥化站不超过5分钟验证
    print("\n验证步骤3: 开车到绥化站不超过5分钟验证")
    if not actual_poi_location:
        print("验证步骤3: 未通过 - 无法获取POI坐标，无法规划驾车路线")
    else:
        # 获取绥化站坐标
        print(f"调用 maps_search_detail(id=\"{station_poi_id}\")")
        station_detail_result = maps_search_detail(id=station_poi_id)

        station_coord = station_location  # 默认使用提供的坐标
        if station_detail_result.error:
            print(f"绥化站详情查询失败: {station_detail_result.error}")
            print(f"使用默认坐标: {station_coord}")
        else:
            if station_detail_result.location:
                station_coord = station_detail_result.location
                print(f"获取到绥化站坐标: {station_coord}")
            else:
                print(f"未找到绥化站坐标，使用默认坐标: {station_coord}")

        # 计算驾车时间
        print(f"调用 maps_driving_by_coordinates(origin=\"{actual_poi_location}\", destination=\"{station_coord}\")")
        driving_result = maps_driving_by_coordinates(
            origin=actual_poi_location,
            destination=station_coord
        )

        if driving_result.error:
            print(f"驾车路线规划失败: {driving_result.error}")
            print("验证步骤3: 未通过")
        else:
            if driving_result.total_duration_seconds is not None:
                duration = driving_result.total_duration_seconds
                if duration <= max_driving_duration_seconds:
                    print(f"验证步骤3: 通过 - 驾车时间 {duration}秒 <= {max_driving_duration_seconds}秒")
                    passed_count += 1
                else:
                    print(f"验证步骤3: 未通过 - 驾车时间 {duration}秒 > {max_driving_duration_seconds}秒")
            else:
                print("验证步骤3: 未通过 - 无法获取驾车时间")

    # 验证步骤4: 评分不低于3.0验证
    print("\n验证步骤4: 评分不低于3.0验证")
    if detail_result.error:
        print("验证步骤4: 未通过 - POI详情查询失败，无法获取评分信息")
    else:
        # 获取rating
        rating = None
        if detail_result.biz_ext and isinstance(detail_result.biz_ext, dict):
            rating_value = detail_result.biz_ext.get("rating")
            if rating_value is not None:
                try:
                    rating = float(rating_value)
                except (ValueError, TypeError):
                    pass

        if rating is not None:
            if rating >= min_rating:
                print(f"验证步骤4: 通过 - POI评分 {rating} >= {min_rating}")
                passed_count += 1
            else:
                print(f"验证步骤4: 未通过 - POI评分 {rating} < {min_rating}")
        else:
            print("验证步骤4: 未通过 - 无法获取POI评分信息")

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
