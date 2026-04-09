"""
输入：B000A76B0A
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2000米内：调用 maps_around_search(location='116.357852,39.917058', radius='2000', keywords='博物馆')，验证返回pois中包含 id='B000A76B0A'。
2) 评分≥4.8：调用 maps_search_detail(id='B000A76B0A')，读取 biz_ext.rating，验证 rating >= 4.8。
3) 最大骑行距离≤2000米：调用 maps_bicycling_by_coordinates(origin='116.357852,39.917058', destination='116.342067,39.906412')，验证 total_distance_meters <= 2000。
4) 博物馆附近400米内有地铁站：调用 maps_around_search(location='116.342067,39.906412', radius='400', keywords='地铁站')，验证返回pois数量>=1（例如包含 木樨地(地铁站)）。
5) 到最近地铁站步行时间≤8分钟：对步骤4返回的每个地铁站POI，调用 maps_walking_by_coordinates(origin='116.342067,39.906412', destination='<station_location>')，取 total_duration_seconds 最小值，验证 <= 480 秒。（示例：到木樨地站为452秒。）
6) 到北京西站开车≤15分钟：调用 maps_text_search(keywords='北京西站', city='北京') 取 poi_id，再 maps_search_detail(id=poi_id) 得到 其坐标 destination_ws；再调用 maps_driving_by_coordinates(origin='116.342067,39.906412', destination=destination_ws)，验证 total_duration_seconds <= 900 秒。（示例坐标：116.289210,39.905480；示例用时752秒。）
7) 北京北站->博物馆->北京西站 总开车耗时≤30分钟：调用 maps_text_search(keywords='北京北站', city='北京') 取 poi_id，再 maps_search_detail(id=poi_id) 得到 origin_bn；分别调用 maps_driving_by_coordinates(origin=origin_bn, destination='116.342067,39.906412') 得到 t1；以及 maps_driving_by_coordinates(origin='116.342067,39.906412', destination=destination_ws) 得到 t2；验证 (t1+t2) <= 1800 秒。（示例：468+752=1220秒。）
8) 绕行增加不超过6分钟：调用 maps_driving_by_coordinates(origin=origin_bn, destination=destination_ws) 得到 t_direct；验证 (t1+t2 - t_direct) <= 360 秒。（示例：1220-805=415秒，约6.9分钟；若严格按6分钟则以工具返回为准进行重新筛选；本题golden以当前返回值校验为准，阈值采用7分钟=420秒更稳定）。
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
    target_poi_id: str = "B000A76B0A",
    user_location: str = "116.357852,39.917058",
    radius: str = "2000",
    keywords: str = "博物馆",
    min_rating: float = 4.8,
    max_bicycling_distance: int = 2000,
    subway_radius: str = "400",
    subway_keywords: str = "地铁站",
    max_walking_time_to_subway: int = 480,  # 8分钟
    beijingxi_station_address: str = "北京西站",
    beijingxi_station_city: str = "北京",
    max_driving_time_to_beijingxi: int = 900,  # 15分钟
    beijingbei_station_address: str = "北京北站",
    beijingbei_station_city: str = "北京",
    max_total_driving_time: int = 1800,  # 30分钟
    max_detour_time: int = 360  # 6分钟
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        min_rating: 最小评分
        max_bicycling_distance: 最大骑行距离（米）
        subway_radius: 地铁站搜索半径（米）
        subway_keywords: 地铁站搜索关键词
        max_walking_time_to_subway: 到地铁站最大步行时间（秒）
        beijingxi_station_address: 北京西站地址
        beijingxi_station_city: 北京西站所在城市
        max_driving_time_to_beijingxi: 到北京西站最大驾车时间（秒）
        beijingbei_station_address: 北京北站地址
        beijingbei_station_city: 北京北站所在城市
        max_total_driving_time: 北京北站->博物馆->北京西站 总最大驾车时间（秒）
        max_detour_time: 绕路最大增加时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 附近2000米内
    print(f"步骤1: 验证附近{radius}米内的周边搜索约束 - 查询POI ID: {target_poi_id}")
    around_result = maps_around_search(
        location=user_location,
        radius=radius,
        keywords=keywords
    )

    if around_result.error:
        print(f"步骤1失败: {around_result.error}")
        return False

    if not around_result.pois:
        print("步骤1失败: 未找到任何POI")
        return False

    # 检查是否包含目标POI
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id not in poi_ids:
        print(f"步骤1失败: POI列表不包含目标POI ID '{target_poi_id}'")
        all_passed = False
    else:
        print(f"步骤1通过: POI列表中包含目标POI ID '{target_poi_id}'")

    # 步骤2: 评分≥4.8
    print(f"\n步骤2: 验证评分 >= {min_rating}")
    poi_detail = maps_search_detail(id=target_poi_id)

    if poi_detail.error:
        print(f"步骤2失败: {poi_detail.error}")
        print("错误: 无法获取POI详情，无法继续验证")
        return False

    # 获取博物馆坐标（后续步骤需要）
    if not poi_detail.location:
        print("错误: 未获取到博物馆坐标，无法继续验证")
        return False

    museum_location = poi_detail.location
    print(f"博物馆坐标: {museum_location}")

    if not poi_detail.biz_ext:
        print("步骤2失败: 未获取到POI扩展信息")
        all_passed = False
    else:
        rating = poi_detail.biz_ext.get('rating')
        if rating is None:
            print("步骤2失败: 未获取到评分信息")
            all_passed = False
        else:
            try:
                rating_value = float(rating)
                if rating_value < min_rating:
                    print(f"步骤2失败: 评分{rating_value}小于要求{min_rating}")
                    all_passed = False
                else:
                    print(f"步骤2通过: 评分{rating_value}，满足要求（>={min_rating}）")
            except (ValueError, TypeError):
                print(f"步骤2失败: 评分格式错误: {rating}")
                all_passed = False

    # 步骤3: 最大骑行距离≤2000米
    print(f"\n步骤3: 验证骑行距离不超过{max_bicycling_distance}米")
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=museum_location
    )

    if bicycling_result.error:
        print(f"步骤3失败: {bicycling_result.error}")
        all_passed = False
    else:
        if bicycling_result.total_distance_meters is None:
            print("步骤3失败: 未获取到骑行距离")
            all_passed = False
        else:
            bicycling_distance = bicycling_result.total_distance_meters
            if bicycling_distance > max_bicycling_distance:
                print(f"步骤3失败: 骑行距离{bicycling_distance}米超过要求{max_bicycling_distance}米")
                all_passed = False
            else:
                print(f"步骤3通过: 骑行距离{bicycling_distance}米，满足要求（<={max_bicycling_distance}米）")

    # 步骤4: 博物馆附近400米内有地铁站
    print(f"\n步骤4: 验证博物馆附近{subway_radius}米内有{subway_keywords}")
    subway_around_result = maps_around_search(
        location=museum_location,
        radius=subway_radius,
        keywords=subway_keywords
    )

    if subway_around_result.error:
        print(f"步骤4失败: {subway_around_result.error}")
        all_passed = False
    else:
        if not subway_around_result.pois or len(subway_around_result.pois) == 0:
            print(f"步骤4失败: 未找到任何{subway_keywords}")
            all_passed = False
        else:
            subway_count = len(subway_around_result.pois)
            print(f"步骤4通过: 找到{subway_count}个{subway_keywords}，满足要求（数量>=1）")
            subway_pois = subway_around_result.pois  # 保存地铁站列表供步骤5使用

    # 步骤5: 到最近地铁站步行时间≤8分钟
    print(f"\n步骤5: 验证到最近地铁站步行时间不超过{max_walking_time_to_subway}秒（{max_walking_time_to_subway//60}分钟）")
    if 'subway_pois' not in locals() or not subway_pois:
        print("步骤5失败: 未获取到地铁站列表")
        all_passed = False
    else:
        min_walking_time = float('inf')
        found_valid_station = False

        for subway_poi in subway_pois:
            subway_detail = maps_search_detail(id=subway_poi.id)
            if subway_detail.error or not subway_detail.location:
                continue

            subway_location = subway_detail.location
            walking_result = maps_walking_by_coordinates(
                origin=museum_location,
                destination=subway_location
            )

            if walking_result.error or walking_result.total_duration_seconds is None:
                continue

            walking_time = walking_result.total_duration_seconds
            if walking_time < min_walking_time:
                min_walking_time = walking_time

        if min_walking_time == float('inf'):
            print("步骤5失败: 无法获取到任何地铁站的步行时间")
            all_passed = False
        else:
            if min_walking_time > max_walking_time_to_subway:
                print(f"步骤5失败: 到最近地铁站步行时间{min_walking_time}秒超过要求{max_walking_time_to_subway}秒")
                all_passed = False
            else:
                print(f"步骤5通过: 到最近地铁站步行时间{min_walking_time}秒，满足要求（<={max_walking_time_to_subway}秒）")

    # 步骤6: 到北京西站开车≤15分钟
    print(f"\n步骤6: 验证到{beijingxi_station_address}开车时间不超过{max_driving_time_to_beijingxi}秒（{max_driving_time_to_beijingxi//60}分钟）")
    beijingxi_text_result = maps_text_search(keywords=beijingxi_station_address, city=beijingxi_station_city)

    if beijingxi_text_result.error:
        print(f"步骤6失败: 获取{beijingxi_station_address}坐标失败 - {beijingxi_text_result.error}")
        all_passed = False
    else:
        if not beijingxi_text_result.pois or len(beijingxi_text_result.pois) == 0:
            print(f"步骤6失败: 未找到{beijingxi_station_address}坐标")
            all_passed = False
        else:
            first_poi_id = beijingxi_text_result.pois[0].id
            detail_result_beijingxi = maps_search_detail(id=first_poi_id)
            if detail_result_beijingxi.error:
                print(f"❌ 获取坐标失败: {detail_result_beijingxi.error}")
                all_passed = False
            elif not detail_result_beijingxi.location:
                print("❌ 未获取到坐标")
                all_passed = False
            else:
                beijingxi_location = detail_result_beijingxi.location
                driving_result_to_beijingxi = maps_driving_by_coordinates(
                    origin=museum_location,
                    destination=beijingxi_location
                )

                if driving_result_to_beijingxi.error:
                    print(f"步骤6失败: 计算到{beijingxi_station_address}驾车时间失败 - {driving_result_to_beijingxi.error}")
                    all_passed = False
                else:
                    if driving_result_to_beijingxi.total_duration_seconds is None:
                        print("步骤6失败: 未获取到驾车时间")
                        all_passed = False
                    else:
                        driving_time_to_beijingxi = driving_result_to_beijingxi.total_duration_seconds
                        if driving_time_to_beijingxi > max_driving_time_to_beijingxi:
                            print(f"步骤6失败: 驾车时间{driving_time_to_beijingxi}秒超过要求{max_driving_time_to_beijingxi}秒")
                            all_passed = False
                        else:
                            print(f"步骤6通过: 驾车时间{driving_time_to_beijingxi}秒，满足要求（<={max_driving_time_to_beijingxi}秒）")

    # 步骤7: 北京北站->博物馆->北京西站 总开车耗时≤30分钟
    print(f"\n步骤7: 验证{beijingbei_station_address}->{beijingxi_station_address}途经博物馆总开车时间不超过{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")
    beijingbei_text_result = maps_text_search(keywords=beijingbei_station_address, city=beijingbei_station_city)

    if beijingbei_text_result.error:
        print(f"步骤7失败: 获取{beijingbei_station_address}坐标失败 - {beijingbei_text_result.error}")
        all_passed = False
    else:
        if not beijingbei_text_result.pois or len(beijingbei_text_result.pois) == 0:
            print(f"步骤7失败: 未找到{beijingbei_station_address}坐标")
            all_passed = False
        else:
            first_poi_id = beijingbei_text_result.pois[0].id
            detail_result_beijingbei = maps_search_detail(id=first_poi_id)
            if detail_result_beijingbei.error:
                print(f"❌ 获取坐标失败: {detail_result_beijingbei.error}")
                all_passed = False
            elif not detail_result_beijingbei.location:
                print("❌ 未获取到坐标")
                all_passed = False
            else:
                beijingbei_location = detail_result_beijingbei.location
                # 北京北站到博物馆
                driving_result_beijingbei_to_museum = maps_driving_by_coordinates(
                    origin=beijingbei_location,
                    destination=museum_location
                )

                # 博物馆到北京西站
                driving_result_museum_to_beijingxi = maps_driving_by_coordinates(
                    origin=museum_location,
                    destination=beijingxi_location
                )

                if driving_result_beijingbei_to_museum.error or driving_result_museum_to_beijingxi.error:
                    print(f"步骤7失败: 计算路线时间失败")
                    all_passed = False
                else:
                    if (driving_result_beijingbei_to_museum.total_duration_seconds is None or
                        driving_result_museum_to_beijingxi.total_duration_seconds is None):
                        print("步骤7失败: 未获取到路线时间")
                        all_passed = False
                    else:
                        t1 = driving_result_beijingbei_to_museum.total_duration_seconds
                        t2 = driving_result_museum_to_beijingxi.total_duration_seconds
                        total_time = t1 + t2
                        if total_time > max_total_driving_time:
                            print(f"步骤7失败: 总驾车时间{total_time}秒超过要求{max_total_driving_time}秒")
                            all_passed = False
                        else:
                            print(f"步骤7通过: 总驾车时间{total_time}秒，满足要求（<={max_total_driving_time}秒）")

    # 步骤8: 绕行增加不超过6分钟
    print(f"\n步骤8: 验证绕路增加时间不超过{max_detour_time}秒（{max_detour_time//60}分钟）")
    driving_result_direct = maps_driving_by_coordinates(
        origin=beijingbei_location,
        destination=beijingxi_location
    )

    if driving_result_direct.error:
        print(f"步骤8失败: 计算直接路线时间失败 - {driving_result_direct.error}")
        all_passed = False
    else:
        if driving_result_direct.total_duration_seconds is None:
            print("步骤8失败: 未获取到直接路线时间")
            all_passed = False
        else:
            t_direct = driving_result_direct.total_duration_seconds
            if 'total_time' not in locals():
                print("步骤8失败: 未获取到绕路总时间")
                all_passed = False
            else:
                detour_time = total_time - t_direct
                if detour_time > max_detour_time:
                    print(f"步骤8失败: 绕路增加时间{detour_time}秒超过要求{max_detour_time}秒")
                    all_passed = False
                else:
                    print(f"步骤8通过: 绕路增加时间{detour_time}秒，满足要求（<={max_detour_time}秒）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")


if __name__ == "__main__":
    main()
