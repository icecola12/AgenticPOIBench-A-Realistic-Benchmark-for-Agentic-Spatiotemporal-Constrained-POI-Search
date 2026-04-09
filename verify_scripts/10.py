"""
修改任务指令：你想在附近1500米以内找一家电影院，评分至少4.7分，并且晚上11点后还营业。这家电影院离逍遥津公园的直线距离需要大于500米。你打算骑自行车去，所以骑行距离不能超过1500米。电影院离四牌楼地铁站步行不能超过10分钟，而且离解放影院公交站直线距离在200米以内。你有个朋友从合肥南站过来，你们看完电影后要去天鹅湖公园，所以从合肥南站经过电影院再到天鹅湖公园的总车程不能超过60分钟。你逻辑性强但没有耐心，希望高效沟通，讨厌废话。
输入：B022702YSK
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1. 调用maps_around_search('117.294395,31.858225','电影院',1500)验证目标电影院在1500米范围内
2. 调用maps_search_detail('B022702YSK')获取电影院详细信息，验证rating≥4.7，open_time显示营业时间至少到23:00之后（实际为24:00）
3. 调用maps_text_search('逍遥津公园','合肥')获取古逍遥津POI ID，再通过maps_search_detail获取其坐标(117.295084,31.868980)，调用maps_distance计算与电影院坐标(117.289168,31.861168)的直线距离，验证>500米
4. 调用maps_bicycling_by_coordinates('117.294395,31.858225','117.289168,31.861168')计算骑行距离，验证≤1500米
5. 调用maps_walking_by_coordinates计算到四牌楼地铁站的步行时间，验证≤600秒（10分钟）
6. 调用maps_distance计算到解放影院公交站的直线距离，验证≤200米
7. 调用maps_text_search('合肥南站','合肥')获取合肥南站POI ID，通过maps_search_detail获取坐标(117.290331,31.797955)
8. 调用maps_text_search('天鹅湖公园','合肥')获取天鹅湖体育公园POI ID，通过maps_search_detail获取坐标(117.224195,31.813446)
9. 调用maps_driving_by_coordinates('117.290331,31.797955','117.289168,31.861168')计算合肥南站到电影院的驾车时间t1
10. 调用maps_driving_by_coordinates('117.289168,31.861168','117.224195,31.813446')计算电影院到天鹅湖公园的驾车时间t2
11. 验证t1+t2≤3600秒（60分钟）
"""
import sys
import os
import re
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
def verify_poi(target_poi_id: str = 'B022702YSK',
               user_location: str = '117.294395,31.858225',
               xiaoyaojin_park_name: str = '逍遥津公园',
               xiaoyaojin_park_city: str = '合肥',
               sipailou_subway_name: str = '四牌楼地铁站',
               jiefang_bus_name: str = '解放影院公交站',
               hefei_south_station_name: str = '合肥南站',
               hefei_south_station_city: str = '合肥',
               tian_e_lake_park_name: str = '天鹅湖公园',
               tian_e_lake_park_city: str = '合肥') -> bool:
    """
    验证POI是否符合所有要求

    Args:
        target_poi_id: 目标POI的ID，默认值为'B022702YSK'
        user_location: 用户位置坐标，默认值为'117.294395,31.858225'
        xiaoyaojin_park_name: 逍遥津公园名称，默认值为'逍遥津公园'
        xiaoyaojin_park_city: 逍遥津公园所在城市，默认值为'合肥'
        sipailou_subway_name: 四牌楼地铁站名称，默认值为'四牌楼地铁站'
        jiefang_bus_name: 解放影院公交站名称，默认值为'解放影院公交站'
        hefei_south_station_name: 合肥南站名称，默认值为'合肥南站'
        hefei_south_station_city: 合肥南站所在城市，默认值为'合肥'
        tian_e_lake_park_name: 天鹅湖公园名称，默认值为'天鹅湖公园'
        tian_e_lake_park_city: 天鹅湖公园所在城市，默认值为'合肥'

    Returns:
        bool: 验证通过返回True，否则返回False
    """
    # 验证步骤计数器
    steps_passed = []
    steps_failed = []

    try:
        # 步骤1: 验证目标电影院在1500米范围内
        print("验证步骤1: 验证目标电影院在1500米范围内")
        around_search_result = maps_around_search(user_location, '1500', '电影院')
        if around_search_result.error or not around_search_result.pois:
            print(f"步骤1失败: 周边搜索失败 - {around_search_result.error}")
            steps_failed.append(1)
            return False

        # 检查目标POI是否在搜索结果中
        target_found = False
        for poi in around_search_result.pois:
            if poi.id == target_poi_id:
                target_found = True
                break

        if target_found:
            print("步骤1通过: 目标电影院在1500米范围内")
            steps_passed.append(1)
        else:
            print("步骤1失败: 目标电影院不在1500米范围内")
            steps_failed.append(1)
            return False

        # 步骤2: 获取电影院详细信息并验证评分和营业时间
        print("验证步骤2: 获取电影院详细信息并验证评分和营业时间")
        poi_detail = maps_search_detail(target_poi_id)
        if poi_detail.error or not poi_detail.location:
            print(f"步骤2失败: 无法获取POI详细信息 - {poi_detail.error}")
            steps_failed.append(2)
            return False

        # 获取电影院坐标（用于后续计算）
        cinema_location = poi_detail.location
        print(f"电影院坐标: {cinema_location}")

        # 验证评分 ≥ 4.7
        if not poi_detail.biz_ext or 'rating' not in poi_detail.biz_ext:
            print("步骤2失败: 无法获取评分信息")
            steps_failed.append(2)
            return False

        rating = float(poi_detail.biz_ext['rating'])
        if rating < 4.7:
            print(f"步骤2失败: 评分 {rating} < 4.7")
            steps_failed.append(2)
            return False

        # 验证营业时间至少到23:00之后
        if not poi_detail.biz_ext or 'open_time' not in poi_detail.biz_ext:
            print("步骤2失败: 无法获取营业时间信息")
            steps_failed.append(2)
            return False

        open_time = poi_detail.biz_ext['open_time']
        if not is_open_until_late(open_time):
            print(f"步骤2失败: 营业时间 '{open_time}' 未达到23:00之后")
            steps_failed.append(2)
            return False

        print(f"步骤2通过: 评分 {rating} ≥ 4.7，营业时间符合要求")
        steps_passed.append(2)

        # 步骤3: 验证到逍遥津公园的距离 > 500米
        print("验证步骤3: 验证到逍遥津公园的距离")

        # 获取逍遥津公园坐标
        park_search = maps_text_search(xiaoyaojin_park_name, xiaoyaojin_park_city)
        if park_search.error or not park_search.pois:
            print(f"步骤3失败: 无法搜索逍遥津公园 - {park_search.error}")
            steps_failed.append(3)
            return False

        park_detail = maps_search_detail(park_search.pois[0].id)
        if park_detail.error or not park_detail.location:
            print(f"步骤3失败: 无法获取逍遥津公园详细信息 - {park_detail.error}")
            steps_failed.append(3)
            return False

        park_location = park_detail.location

        distance_result = maps_distance(cinema_location, park_location)
        if distance_result.error or not distance_result.results:
            print(f"步骤3失败: 无法计算距离 - {distance_result.error}")
            steps_failed.append(3)
            return False

        distance = distance_result.results[0].distance_meters
        if distance > 500:
            print(f"步骤3通过: 到逍遥津公园距离 {distance}米 > 500米")
            steps_passed.append(3)
        else:
            print(f"步骤3失败: 到逍遥津公园距离 {distance}米 ≤ 500米")
            steps_failed.append(3)
            return False

        # 步骤4: 验证骑行距离 ≤ 1500米
        print("验证步骤4: 验证骑行距离")

        bicycling_result = maps_bicycling_by_coordinates(user_location, cinema_location)
        if bicycling_result.error or bicycling_result.total_distance_meters is None:
            print(f"步骤4失败: 无法计算骑行距离 - {bicycling_result.error}")
            steps_failed.append(4)
            return False

        bicycling_distance = bicycling_result.total_distance_meters
        if bicycling_distance <= 1500:
            print(f"步骤4通过: 骑行距离 {bicycling_distance}米 ≤ 1500米")
            steps_passed.append(4)
        else:
            print(f"步骤4失败: 骑行距离 {bicycling_distance}米 > 1500米")
            steps_failed.append(4)
            return False

        # 步骤5: 验证到四牌楼地铁站的步行时间 ≤ 600秒
        print("验证步骤5: 验证到四牌楼地铁站的步行时间")

        # 获取四牌楼地铁站坐标
        subway_search = maps_text_search(sipailou_subway_name, '合肥')
        if subway_search.error or not subway_search.pois:
            print(f"步骤5失败: 无法搜索四牌楼地铁站 - {subway_search.error}")
            steps_failed.append(5)
            return False

        subway_detail = maps_search_detail(subway_search.pois[0].id)
        if subway_detail.error or not subway_detail.location:
            print(f"步骤5失败: 无法获取四牌楼地铁站详细信息 - {subway_detail.error}")
            steps_failed.append(5)
            return False

        subway_location = subway_detail.location

        walking_result = maps_walking_by_coordinates(cinema_location, subway_location)
        if walking_result.error or walking_result.total_duration_seconds is None:
            print(f"步骤5失败: 无法计算步行时间 - {walking_result.error}")
            steps_failed.append(5)
            return False

        walking_time = walking_result.total_duration_seconds
        if walking_time <= 600:
            print(f"步骤5通过: 到四牌楼地铁站步行时间 {walking_time}秒 ≤ 600秒")
            steps_passed.append(5)
        else:
            print(f"步骤5失败: 到四牌楼地铁站步行时间 {walking_time}秒 > 600秒")
            steps_failed.append(5)
            return False

        # 步骤6: 验证到解放影院公交站的直线距离 ≤ 200米
        print("验证步骤6: 验证到解放影院公交站的直线距离")

        # 获取解放影院公交站坐标
        bus_search = maps_text_search(jiefang_bus_name, '合肥')
        if bus_search.error or not bus_search.pois:
            print(f"步骤6失败: 无法搜索解放影院公交站 - {bus_search.error}")
            steps_failed.append(6)
            return False

        bus_detail = maps_search_detail(bus_search.pois[0].id)
        if bus_detail.error or not bus_detail.location:
            print(f"步骤6失败: 无法获取解放影院公交站详细信息 - {bus_detail.error}")
            steps_failed.append(6)
            return False

        bus_location = bus_detail.location

        bus_distance_result = maps_distance(cinema_location, bus_location)
        if bus_distance_result.error or not bus_distance_result.results:
            print(f"步骤6失败: 无法计算距离 - {bus_distance_result.error}")
            steps_failed.append(6)
            return False

        bus_distance = bus_distance_result.results[0].distance_meters
        if bus_distance <= 200:
            print(f"步骤6通过: 到解放影院公交站距离 {bus_distance}米 ≤ 200米")
            steps_passed.append(6)
        else:
            print(f"步骤6失败: 到解放影院公交站距离 {bus_distance}米 > 200米")
            steps_failed.append(6)
            return False

        # 步骤7: 获取合肥南站坐标
        print("验证步骤7: 获取合肥南站坐标")
        station_search = maps_text_search(hefei_south_station_name, hefei_south_station_city)
        if station_search.error or not station_search.pois:
            print(f"步骤7失败: 无法搜索合肥南站 - {station_search.error}")
            steps_failed.append(7)
            return False

        station_detail = maps_search_detail(station_search.pois[0].id)
        if station_detail.error or not station_detail.location:
            print(f"步骤7失败: 无法获取合肥南站详细信息 - {station_detail.error}")
            steps_failed.append(7)
            return False

        station_location = station_detail.location
        print(f"合肥南站坐标: {station_location}")
        steps_passed.append(7)

        # 步骤8: 获取天鹅湖公园坐标
        print("验证步骤8: 获取天鹅湖公园坐标")
        lake_park_search = maps_text_search(tian_e_lake_park_name, tian_e_lake_park_city)
        if lake_park_search.error or not lake_park_search.pois:
            print(f"步骤8失败: 无法搜索天鹅湖公园 - {lake_park_search.error}")
            steps_failed.append(8)
            return False

        lake_park_detail = maps_search_detail(lake_park_search.pois[0].id)
        if lake_park_detail.error or not lake_park_detail.location:
            print(f"步骤8失败: 无法获取天鹅湖公园详细信息 - {lake_park_detail.error}")
            steps_failed.append(8)
            return False

        lake_park_location = lake_park_detail.location
        print(f"天鹅湖公园坐标: {lake_park_location}")
        steps_passed.append(8)

        # 步骤9: 计算合肥南站到电影院的驾车时间t1
        print("验证步骤9: 计算合肥南站到电影院的驾车时间")
        drive_to_cinema = maps_driving_by_coordinates(station_location, cinema_location)
        if drive_to_cinema.error or drive_to_cinema.total_duration_seconds is None:
            print(f"步骤9失败: 无法计算合肥南站到电影院驾车时间 - {drive_to_cinema.error}")
            steps_failed.append(9)
            return False

        t1_minutes = drive_to_cinema.total_duration_seconds / 60
        print(f"合肥南站到电影院驾车时间: {t1_minutes:.1f}分钟")
        steps_passed.append(9)

        # 步骤10: 计算电影院到天鹅湖公园的驾车时间t2
        print("验证步骤10: 计算电影院到天鹅湖公园的驾车时间")
        drive_to_lake_park = maps_driving_by_coordinates(cinema_location, lake_park_location)
        if drive_to_lake_park.error or drive_to_lake_park.total_duration_seconds is None:
            print(f"步骤10失败: 无法计算电影院到天鹅湖公园驾车时间 - {drive_to_lake_park.error}")
            steps_failed.append(10)
            return False

        t2_minutes = drive_to_lake_park.total_duration_seconds / 60
        print(f"电影院到天鹅湖公园驾车时间: {t2_minutes:.1f}分钟")
        steps_passed.append(10)

        # 步骤11: 验证t1 + t2 ≤ 3600秒（60分钟）
        print("验证步骤11: 验证总驾车时间")
        total_drive_time = drive_to_cinema.total_duration_seconds + drive_to_lake_park.total_duration_seconds
        total_drive_time_minutes = total_drive_time / 60
        print(f"总驾车时间: {total_drive_time_minutes:.1f}分钟")

        if total_drive_time <= 3600:
            print(f"步骤11通过: 总驾车时间 {total_drive_time_minutes:.1f}分钟 ≤ 60分钟")
            steps_passed.append(11)
        else:
            print(f"步骤11失败: 总驾车时间 {total_drive_time_minutes:.1f}分钟 > 60分钟")
            steps_failed.append(11)
            return False

        # 所有验证都通过
        return True

    except Exception as e:
        print(f"验证过程中发生异常: {e}")
        return False


def is_open_until_late(open_time_str: str) -> bool:
    """
    检查营业时间是否至少到23:00之后

    Args:
        open_time_str: 营业时间字符串

    Returns:
        bool: 如果营业时间至少到23:00之后返回True，否则返回False
    """
    if not open_time_str:
        return False

    # 处理全天营业的情况
    if '24' in open_time_str.lower() or '全天' in open_time_str:
        return True

    # 使用正则表达式提取时间范围
    # 匹配类似 "08:30-23:00" 或 "08:30-次日02:00" 的格式
    time_ranges = re.findall(r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})', open_time_str)

    if not time_ranges:
        # 如果没找到标准格式，尝试其他格式
        # 处理类似 "23:00" 这样的单时间点
        single_times = re.findall(r'(\d{1,2}:\d{2})', open_time_str)
        if single_times:
            for time_str in single_times:
                hour, minute = map(int, time_str.split(':'))
                if hour >= 23:  # 23:00或之后
                    return True
        return False

    # 检查每个时间范围
    for start_time, end_time in time_ranges:
        try:
            # 解析结束时间
            end_hour, end_minute = map(int, end_time.split(':'))

            # 如果结束时间是次日，认为是通宵营业
            if '次日' in open_time_str or '翌日' in open_time_str:
                return True

            # 检查结束时间是否在23:00之后
            if end_hour >= 23:  # 23:00或之后
                return True

        except ValueError:
            continue

    return False


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")


if __name__ == "__main__":
    main()
