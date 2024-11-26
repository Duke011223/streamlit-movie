import streamlit as st
import pandas as pd
import hashlib
import os

# CSV 파일 로드
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("movie_data.csv", encoding='cp949')
        df.columns = df.columns.str.strip().str.lower()  # 컬럼명 공백 제거 및 소문자화
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

def save_users(users):
    pd.DataFrame(users).to_csv("movie_users.csv", index=False, encoding='cp949')

def load_users():
    path = "movie_users.csv"
    if os.path.exists(path):
        return pd.read_csv(path, encoding='cp949').to_dict('records')
    return []

def save_ratings(ratings):
    pd.DataFrame(ratings).to_csv("movie_ratings.csv", index=False, encoding='cp949')

def load_ratings():
    path = "movie_ratings.csv"
    if os.path.exists(path):
        return pd.read_csv(path, encoding='cp949').to_dict('records')
    return []

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    st.set_page_config(page_title="영화 추천 시스템", layout="wide")
    st.title("🎬 영화 추천 및 검색 시스템")

    df = load_data()
    users = load_users()
    ratings = load_ratings()

    if 'user' not in st.session_state:
        st.session_state.user = None
        st.session_state.role = None

    # 포스터 파일 폴더 경로
    poster_folder = "poster_file"

    # 사이드바 사용자 인증
    with st.sidebar:
        st.header("👤 사용자 인증")
        if st.session_state.user:
            st.write(f"환영합니다, **{st.session_state.user}님!**")
            if st.button("로그아웃"):
                st.session_state.user = None
                st.session_state.role = None
                st.success("로그아웃 성공!")
        else:
            choice = st.radio("로그인/회원가입", ["로그인", "회원가입"])
            if choice == "로그인":
                username = st.text_input("사용자명")
                password = st.text_input("비밀번호", type="password")
                if st.button("로그인"):
                    user = next((u for u in users if u['username'] == username and u['password'] == hash_password(password)), None)
                    if user:
                        st.session_state.user = username
                        st.session_state.role = user['role']
                        st.success("로그인 성공!")
                    else:
                        st.error("잘못된 사용자명 또는 비밀번호입니다.")
            else:
                new_username = st.text_input("새 사용자명")
                new_password = st.text_input("새 비밀번호", type="password")
                if st.button("회원가입"):
                    if any(u['username'] == new_username for u in users):
                        st.error("이미 존재하는 사용자명입니다.")
                    else:
                        users.append({'username': new_username, 'password': hash_password(new_password), 'role': 'user'})
                        save_users(users)
                        st.success("회원가입 성공! 이제 로그인할 수 있습니다.")

        st.markdown("---")

    # 메인 영역
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📚 영화 검색", "⭐ 추천 영화", "📈 나의 활동", "🔧 사용자 계정 관리", "👑 관리자 보기"])

    # 영화 검색
    with tab1:
        st.header("🎥 영화 검색")
        search_term = st.text_input("🔍 검색", placeholder="영화 제목을 입력하세요...")
        genre_filter = st.selectbox("🎭 장르 필터", options=["모든 장르"] + df['genre'].unique().tolist())

        # 필터링 및 페이지네이션
        filtered_df = df[df['title'].str.contains(search_term, case=False)]
        if genre_filter != "모든 장르":
            filtered_df = filtered_df[filtered_df['genre'] == genre_filter]

        total_movies = len(filtered_df)
        if total_movies == 0:
            st.warning("검색 결과가 없습니다.")
        else:
            page_size = 5
            total_pages = (total_movies // page_size) + (1 if total_movies % page_size != 0 else 0)
            page = st.number_input("페이지 번호", min_value=1, max_value=total_pages, value=1)

            start_idx = (page - 1) * page_size
            end_idx = min(page * page_size, total_movies)

            for _, movie in filtered_df.iloc[start_idx:end_idx].iterrows():
                st.subheader(movie['title'])

                # 포스터 파일 경로
                poster_path = os.path.join(poster_folder, movie.get('poster_file', ''))
                if os.path.exists(poster_path) and pd.notna(movie.get('poster_file')):
                    st.image(poster_path, width=200)  # 이미지 표시
                else:
                    st.write("포스터 이미지가 없습니다.")  # 이미지가 없을 경우 메시지 출력

                # 영화 정보 출력
                st.write(f"**영화 ID**: {movie['movie_id']}")
                st.write(f"**제작사**: {movie['distributor']}")
                st.write(f"**감독**: {movie['director']}")
                st.write(f"**배우**: {movie['actor']}")
                st.write(f"**장르**: {movie['genre']}")
                st.write(f"**개봉일**: {movie['release_date']}")

                running_time = movie.get('running_time', '정보 없음')
                if running_time != '정보 없음':
                    try:
                        running_time = int(running_time)
                        st.write(f"**상영 시간**: {running_time}분")
                    except ValueError:
                        st.write("**상영 시간**: 정보 없음")
                else:
                    st.write(f"**상영 시간**: {running_time}분")

                st.write(f"**영화 평점**: {movie['rating']}")
                st.write(f"**현재 상태**: {movie['running_state']}")
                st.markdown("---")

                # 영화에 대한 평점 표시
                movie_ratings = [r['rating'] for r in ratings if r['movie'] == movie['title']]
                if movie_ratings:
                    avg_rating = round(sum(movie_ratings) / len(movie_ratings), 2)
                    st.write(f"사이트 평점: {'⭐' * int(avg_rating)} ({avg_rating}/10)")
                else:
                    st.write("아직 평점이 없습니다.")

                movie_reviews = [r['review'] for r in ratings if r['movie'] == movie['title'] and r.get('review') is not None]
                if movie_reviews:
                    st.write("리뷰:")
                    for review in movie_reviews:
                        st.write(f"- {review}")
                else:
                    st.write("아직 리뷰가 없습니다.")

                if st.session_state.user:
                    if any(r['username'] == st.session_state.user and r['movie'] == movie['title'] for r in ratings):
                        st.info("이미 이 영화에 평점과 리뷰를 남겼습니다.")
                    else:
                        rating = st.number_input(f"평점을 선택하세요 ({movie['title']})", min_value=0.0, max_value=10.0, step=0.1, format="%.2f")
                        review = st.text_area(f"리뷰를 작성하세요 ({movie['title']})", placeholder="영화를 보고 느낀 점을 적어보세요...")

                        if st.button(f"'{movie['title']}' 평점 및 리뷰 남기기", key=f"rate-review-{movie['title']}"):
                            ratings.append({
                                'username': st.session_state.user, 
                                'movie': movie['title'], 
                                'rating': round(rating, 2),
                                'review': review if review else None
                            })
                            save_ratings(ratings)
                            st.success("평점과 리뷰가 저장되었습니다.")

    # 추천 영화
    with tab2:
        st.header("⭐ 추천 영화")

        if not st.session_state.user:
            st.warning("로그인 후 추천 영화를 확인할 수 있습니다.")
        else:
            # 추천 기준 선택
            recommendation_type = st.selectbox(
                "추천 기준을 선택하세요",
                ["가장 많은 리뷰 수", "가장 높은 평점", "사용자 별 점 평균 순"]
            )

            # 영화별 리뷰 및 평점 데이터 처리
            movie_review_counts = {}
            movie_rating_sums = {}
            movie_rated_users = {}

            for r in ratings:
                movie = r['movie']
                movie_review_counts[movie] = movie_review_counts.get(movie, 0) + (1 if r.get('review') else 0)
                movie_rating_sums[movie] = movie_rating_sums.get(movie, 0) + r['rating']
                movie_rated_users[movie] = movie_rated_users.get(movie, 0) + 1

            # 영화 데이터와 리뷰 데이터 병합
            df['review_count'] = df['title'].map(movie_review_counts).fillna(0).astype(int)
            df['total_rating'] = df['title'].map(movie_rating_sums).fillna(0.0)
            df['user_count'] = df['title'].map(movie_rated_users).fillna(0).astype(int)
            df['avg_star_rating'] = (df['total_rating'] / df['user_count']).fillna(0.0)

            # 추천 정렬 기준에 따라 정렬
            if recommendation_type == "가장 많은 리뷰 수":
                recommended_movies = df.sort_values(by='review_count', ascending=False)
            elif recommendation_type == "가장 높은 평점":
                recommended_movies = df.sort_values(by='rating', ascending=False)
            elif recommendation_type == "사용자 별 점 평균 순":
                recommended_movies = df.sort_values(by='avg_star_rating', ascending=False)

            # 추천 영화 출력
            top_n = 1  # 추천 영화 개수
            for _, movie in recommended_movies.head(top_n).iterrows():
                st.subheader(movie['title'])

                # 포스터 출력
                poster_path = os.path.join(poster_folder, movie.get('poster_file', ''))
                if os.path.exists(poster_path) and pd.notna(movie.get('poster_file')):
                    st.image(poster_path, width=200)
                else:
                    st.write("포스터 이미지가 없습니다.")

                # 영화 정보 출력
                st.write(f"**평점**: {movie['rating']}")
                st.write(f"**장르**: {movie['genre']}")
                st.write(f"**상영 시간**: {movie.get('running_time', '정보 없음')}")
                st.write(f"**개봉일**: {movie['release_date']}")
                st.write(f"**리뷰 수**: {movie['review_count']}개")
                st.write(f"**사용자 평균 별 점수**: {round(movie['avg_star_rating'], 2)}")

                # 사용자 리뷰 출력
                movie_reviews = [
                    (r['username'], r['review']) for r in ratings 
                    if r['movie'] == movie['title'] and r.get('review') is not None
                ]
                if movie_reviews:
                    st.write("리뷰:")
                    for username, review in movie_reviews:
                        st.write(f"- **{username}**: {review}")
                else:
                    st.write("아직 리뷰가 없습니다.")
                st.markdown("---")


    # 나의 활동
    with tab3:
        st.header("📈 나의 활동")
        if st.session_state.user:
            user_reviews = [r for r in ratings if r['username'] == st.session_state.user]
            if user_reviews:
                st.write("내가 남긴 리뷰:")
                for review in user_reviews:
                    st.write(f"- **영화**: {review['movie']}, **평점**: {review['rating']}, **리뷰**: {review.get('review', '없음')}")
            else:
                st.write("아직 리뷰를 작성하지 않았습니다.")
        else:
            st.warning("로그인 후 활동을 확인할 수 있습니다.")
    # 사용자 계정 관리
    with tab4:
        st.header("🔧 사용자 계정 관리")
        if st.session_state.user:
            user = next(u for u in users if u['username'] == st.session_state.user)
            new_password = st.text_input("새 비밀번호", type="password")
            if st.button("비밀번호 변경"):
                user['password'] = hash_password(new_password)
                save_users(users)
                st.success("비밀번호가 변경되었습니다.")
        else:
            st.warning("로그인 후 계정 관리가 가능합니다.")

    # 관리자 보기
    with tab5:
        st.header("👑 관리자 보기")
        if st.session_state.role == 'admin':
            st.subheader("📋 회원 정보")
            user_info = pd.DataFrame(users)
            st.dataframe(user_info)

            st.markdown("---")
            st.subheader("📝 사용자 리뷰 관리")

            admin_ratings = load_ratings()
            if admin_ratings:
                for r in admin_ratings:
                    st.write(f"**사용자**: {r['username']}")
                    st.write(f"**영화**: {r['movie']}")
                    st.write(f"**평점**: {r['rating']}")
                    st.write(f"**리뷰**: {r['review'] if r['review'] else '없음'}")
                    st.markdown("---")

                    # 리뷰 수정 기능
                    edit_review = st.expander(f"수정하기 ({r['username']} - {r['movie']})", expanded=False)
                    with edit_review:
                        new_rating = st.number_input(
                            f"새 평점 ({r['username']} - {r['movie']})", 
                            min_value=0.0, 
                            max_value=10.0, 
                            step=0.1, 
                            value=r['rating'], 
                            format="%.2f"
                        )
                        new_review = st.text_area(
                            f"새 리뷰 ({r['username']} - {r['movie']})", 
                            value=r['review'] if r['review'] else "", 
                            height=150
                        )

                        if st.button(f"수정 저장 ({r['username']} - {r['movie']})", key=f"save-edit-review-{r['username']}-{r['movie']}"):
                            # 수정된 평점 및 리뷰 업데이트
                            r['rating'] = new_rating
                            r['review'] = new_review if new_review else None

                            # 수정된 리뷰 저장
                            save_ratings(admin_ratings)
                            st.success(f"리뷰가 성공적으로 수정되었습니다. ({r['movie']})")
            else:
                st.write("현재 리뷰가 없습니다.")
        else:
            st.warning("관리자만 볼 수 있는 페이지입니다.")




if __name__ == "__main__":
    main()
