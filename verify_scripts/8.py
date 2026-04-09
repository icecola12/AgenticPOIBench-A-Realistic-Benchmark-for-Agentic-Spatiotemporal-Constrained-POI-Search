"""
修改任务指令：你想在附近3000米以内找一个电竞馆，评分不低于4.3分，人均消费不超过70元。电竞馆离中国矿业大学文昌校区的直线距离需要大于500米。你步行去电竞馆的路上，至少需要存在一个途径点满足附近300米内要有餐厅。电竞馆附近1500米内的地铁站中，得有一个走过去步行距离不超过800米。你有一个朋友从徐州火车站开车过来，你们约好先在电竞馆碰头，然后一起去徐州博物馆。从火车站经电竞馆到博物馆的总开车时间不能超过40分钟，而且这样绕路比直接从火车站去博物馆增加的时间不能超过20分钟。另外，电竞馆到师范大学地铁站的步行时间要在10分钟以内。你说话非常有条理和注重细节
输入：B0FFHEN9OM
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('117.189269,34.214618', '电竞馆', 3000)或maps_around_search('117.189269,34.214618', '游戏厅', 3000)搜索候选POI
2. 对目标POI调用maps_search_detail('B0FFHEN9OM')获取详细信息
3. 验证biz_ext.rating ≥ 4.3
4. 验证biz_ext.cost ≤ 70元（实际为63元）
5. 调用maps_distance('117.188406,34.191919', '117.201227,34.219010')验证到中国矿业大学文昌校区距离 > 500米
6. 调用maps_walking_by_coordinates('117.189269,34.214618', '117.188406,34.191919')获取步行路线步骤点
7. 对每个步骤点调用maps_around_search(步骤点坐标, '餐厅', 300)验证至少一个步骤点附近300米内有餐厅
8. 调用maps_around_search('117.188406,34.191919', '地铁站', 1500)获取附近地铁站
9. 对每个地铁站调用maps_walking_by_coordinates计算步行距离，验证至少一个地铁站步行距离 ≤ 800米
10. 调用maps_driving_by_coordinates('117.207930,34.265209', '117.188406,34.191919')计算徐州火车站到电竞馆驾车时间t1
11. 调用maps_driving_by_coordinates('117.188406,34.191919', '117.186653,34.251058')计算电竞馆到徐州博物馆驾车时间t2
12. 验证t1 + t2 ≤ 40分钟
13. 调用maps_driving_by_coordinates('117.207930,34.265209', '117.186653,34.251058')计算直达驾车时间t3
14. 验证(t1 + t2) - t3 ≤ 20分钟
15. 调用maps_walking_by_coordinates('117.188406,34.191919', '117.189867,34.194137')计算到师范大学地铁站步行时间，验证 ≤ 10分钟
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
    maps_driving_by_coordinates,
    maps_geo,
    maps_walking_by_coordinates,
    maps_around_search,
    maps_text_search,
    maps_bicycling_by_coordinates
)

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(target_poi_id: str = 'B0FFHEN9OM') -> bool:
    """
    验证POI是否符合所有要求

    Args:
        target_poi_id: 目标POI的ID，默认值为'B0FFHEN9OM'

    Returns:
        bool: 验证通过返回True，否则返回False
    """
    # 验证步骤计数器
    steps_passed = []
    steps_failed = []

    try:
        # 步骤2: 获取POI详细信息
        print("验证步骤2: 获取POI详细信息")
        poi_detail = maps_search_detail(target_poi_id)
        if poi_detail.error or not poi_detail.location:
            print(f"步骤2失败: 无法获取POI详细信息 - {poi_detail.error}")
            steps_failed.append(2)
            return False
        steps_passed.append(2)

        # 获取电竞馆坐标（用于后续距离计算）
        eshop_location = poi_detail.location
        print(f"电竞馆坐标: {eshop_location}")

        # 步骤3: 验证评分 ≥ 4.3
        print("验证步骤3: 评分验证")
        if not poi_detail.biz_ext or 'rating' not in poi_detail.biz_ext:
            print("步骤3失败: 无法获取评分信息")
            steps_failed.append(3)
            return False

        rating = float(poi_detail.biz_ext['rating'])
        if rating >= 4.3:
            print(f"步骤3通过: 评分 {rating} ≥ 4.3")
            steps_passed.append(3)
        else:
            print(f"步骤3失败: 评分 {rating} < 4.3")
            steps_failed.append(3)
            return False

        # 步骤4: 验证人均消费 ≤ 70元
        print("验证步骤4: 人均消费验证")
        if not poi_detail.biz_ext or 'cost' not in poi_detail.biz_ext:
            print("步骤4失败: 无法获取人均消费信息")
            steps_failed.append(4)
            return False

        cost = float(poi_detail.biz_ext['cost'])
        if cost <= 70:
            print(f"步骤4通过: 人均消费 {cost}元 ≤ 70元")
            steps_passed.append(4)
        else:
            print(f"步骤4失败: 人均消费 {cost}元 > 70元")
            steps_failed.append(4)
            return False

        # 步骤5: 验证到中国矿业大学文昌校区的距离 > 500米
        print("验证步骤5: 距离中国矿业大学文昌校区验证")
        university_location = '117.201227,34.219010'  # 中国矿业大学文昌校区坐标
        distance_result = maps_distance(eshop_location, university_location)
        if distance_result.error or not distance_result.results:
            print(f"步骤5失败: 无法计算距离 - {distance_result.error}")
            steps_failed.append(5)
            return False

        distance = distance_result.results[0].distance_meters
        if distance > 500:
            print(f"步骤5通过: 距离 {distance}米 > 500米")
            steps_passed.append(5)
        else:
            print(f"步骤5失败: 距离 {distance}米 ≤ 500米")
            steps_failed.append(5)
            return False

        # 步骤6: 获取步行路线步骤点
        print("验证步骤6: 获取步行路线步骤点")
        user_location = '117.189269,34.214618'  # 用户位置坐标
        walking_route = maps_walking_by_coordinates(user_location, eshop_location)
        if walking_route.error or not walking_route.steps:
            print(f"步骤6失败: 无法获取步行路线 - {walking_route.error}")
            steps_failed.append(6)
            return False
        steps_passed.append(6)

        # 步骤7: 验证至少一个步骤点附近300米内有餐厅
        print("验证步骤7: 验证途径点附近餐厅")
        has_restaurant_nearby = False
        for i, step in enumerate(walking_route.steps):
            step_location = step.to_coordinates
            restaurant_search = maps_around_search(step_location, '300', '餐厅')
            if not restaurant_search.error and restaurant_search.pois:
                has_restaurant_nearby = True
                print(f"步骤7通过: 步骤点{i+1}附近300米内有餐厅")
                break

        if has_restaurant_nearby:
            steps_passed.append(7)
        else:
            print("步骤7失败: 所有步骤点附近300米内都没有餐厅")
            steps_failed.append(7)
            return False

        # 步骤8: 获取附近1500米内的地铁站
        print("验证步骤8: 获取附近地铁站")
        subway_search = maps_around_search(eshop_location, '1500', '地铁站')
        if subway_search.error:
            print(f"步骤8失败: 无法搜索地铁站 - {subway_search.error}")
            steps_failed.append(8)
            return False

        subway_stations = subway_search.pois if subway_search.pois else []
        if not subway_stations:
            print("步骤8失败: 附近1500米内没有地铁站")
            steps_failed.append(8)
            return False
        steps_passed.append(8)

        # 步骤9: 验证至少一个地铁站步行距离 ≤ 800米
        print("验证步骤9: 验证地铁站步行距离")
        has_nearby_subway = False
        for station in subway_stations:
            if station.location:
                walking_to_subway = maps_walking_by_coordinates(eshop_location, station.location)
                if not walking_to_subway.error and walking_to_subway.total_duration_seconds:
                    duration_minutes = walking_to_subway.total_duration_seconds / 60
                    if duration_minutes <= 10:  # 800米大约对应10分钟步行时间
                        has_nearby_subway = True
                        print(f"步骤9通过: 地铁站 '{station.name}' 步行距离约{duration_minutes:.1f}分钟 ≤ 10分钟")
                        break

        if has_nearby_subway:
            steps_passed.append(9)
        else:
            print("步骤9失败: 所有地铁站步行距离都 > 10分钟")
            steps_failed.append(9)
            return False

        # 步骤10-11: 计算驾车时间
        print("验证步骤10-11: 计算驾车时间")
        train_station = '117.207930,34.265209'  # 徐州火车站
        museum = '117.186653,34.251058'  # 徐州博物馆

        # 计算徐州火车站到电竞馆驾车时间
        drive_to_eshop = maps_driving_by_coordinates(train_station, eshop_location)
        if drive_to_eshop.error or not drive_to_eshop.total_duration_seconds:
            print(f"步骤10失败: 无法计算火车站到电竞馆驾车时间 - {drive_to_eshop.error}")
            steps_failed.append(10)
            return False

        t1_minutes = drive_to_eshop.total_duration_seconds / 60
        print(f"火车站到电竞馆驾车时间: {t1_minutes:.1f}分钟")

        # 计算电竞馆到徐州博物馆驾车时间
        drive_to_museum = maps_driving_by_coordinates(eshop_location, museum)
        if drive_to_museum.error or not drive_to_museum.total_duration_seconds:
            print(f"步骤11失败: 无法计算电竞馆到博物馆驾车时间 - {drive_to_museum.error}")
            steps_failed.append(11)
            return False

        t2_minutes = drive_to_museum.total_duration_seconds / 60
        print(f"电竞馆到博物馆驾车时间: {t2_minutes:.1f}分钟")

        # 步骤12: 验证t1 + t2 ≤ 40分钟
        total_drive_time = t1_minutes + t2_minutes
        print(f"验证步骤12: 总驾车时间 {total_drive_time:.1f}分钟")
        if total_drive_time <= 40:
            print(f"步骤12通过: 总驾车时间 {total_drive_time:.1f}分钟 ≤ 40分钟")
            steps_passed.append(12)
        else:
            print(f"步骤12失败: 总驾车时间 {total_drive_time:.1f}分钟 > 40分钟")
            steps_failed.append(12)
            return False

        # 步骤13: 计算直达驾车时间
        print("验证步骤13: 计算直达驾车时间")
        direct_drive = maps_driving_by_coordinates(train_station, museum)
        if direct_drive.error or not direct_drive.total_duration_seconds:
            print(f"步骤13失败: 无法计算直达驾车时间 - {direct_drive.error}")
            steps_failed.append(13)
            return False

        t3_minutes = direct_drive.total_duration_seconds / 60
        print(f"直达驾车时间: {t3_minutes:.1f}分钟")

        # 步骤14: 验证(t1 + t2) - t3 ≤ 20分钟
        detour_time = total_drive_time - t3_minutes
        print(f"验证步骤14: 绕路增加时间 {detour_time:.1f}分钟")
        if detour_time <= 20:
            print(f"步骤14通过: 绕路增加时间 {detour_time:.1f}分钟 ≤ 20分钟")
            steps_passed.append(14)
        else:
            print(f"步骤14失败: 绕路增加时间 {detour_time:.1f}分钟 > 20分钟")
            steps_failed.append(14)
            return False

        # 步骤15: 验证到师范大学地铁站步行时间 ≤ 10分钟
        print("验证步骤15: 验证到师范大学地铁站步行时间")
        normal_university_subway = '117.189867,34.194137'  # 师范大学地铁站
        walking_to_normal_subway = maps_walking_by_coordinates(eshop_location, normal_university_subway)
        if walking_to_normal_subway.error or not walking_to_normal_subway.total_duration_seconds:
            print(f"步骤15失败: 无法计算步行时间 - {walking_to_normal_subway.error}")
            steps_failed.append(15)
            return False

        walking_time_minutes = walking_to_normal_subway.total_duration_seconds / 60
        if walking_time_minutes <= 10:
            print(f"步骤15通过: 步行时间 {walking_time_minutes:.1f}分钟 ≤ 10分钟")
            steps_passed.append(15)
        else:
            print(f"步骤15失败: 步行时间 {walking_time_minutes:.1f}分钟 > 10分钟")
            steps_failed.append(15)
            return False

        # 所有验证都通过
        return True

    except Exception as e:
        print(f"验证过程中发生异常: {e}")
        return False


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")  


if __name__ == "__main__":
    main()
