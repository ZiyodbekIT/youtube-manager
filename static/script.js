document.addEventListener("DOMContentLoaded", () => {

    const sidebar =
        document.getElementById("sidebar");

    const sidebarOverlay =
        document.getElementById("sidebarOverlay");

    const mobileMenuButton =
        document.getElementById("mobileMenuButton");

    const sidebarClose =
        document.getElementById("sidebarClose");


    function openSidebar() {

        if (!sidebar) {
            return;
        }

        sidebar.classList.add("open");

        if (sidebarOverlay) {
            sidebarOverlay.classList.add("show");
        }
    }


    function closeSidebar() {

        if (!sidebar) {
            return;
        }

        sidebar.classList.remove("open");

        if (sidebarOverlay) {
            sidebarOverlay.classList.remove("show");
        }
    }


    if (mobileMenuButton) {
        mobileMenuButton.addEventListener(
            "click",
            openSidebar
        );
    }


    if (sidebarClose) {
        sidebarClose.addEventListener(
            "click",
            closeSidebar
        );
    }


    if (sidebarOverlay) {
        sidebarOverlay.addEventListener(
            "click",
            closeSidebar
        );
    }


    /*
        SIDEBAR ACTIVE ANIMATION
    */

    const menuItems =
        document.querySelectorAll(".menu-item");


    menuItems.forEach((item) => {

        item.addEventListener("click", () => {

            menuItems.forEach((menuItem) => {
                menuItem.classList.remove("active");
            });

            item.classList.add("active");

            if (window.innerWidth <= 900) {
                closeSidebar();
            }
        });
    });


    /*
        CTRL + K SEARCH
    */

    const globalSearch =
        document.getElementById("globalSearch");


    document.addEventListener(
        "keydown",
        (event) => {

            if (
                event.ctrlKey &&
                event.key.toLowerCase() === "k"
            ) {
                event.preventDefault();

                if (globalSearch) {
                    globalSearch.focus();
                    globalSearch.select();
                }
            }
        }
    );


    /*
        CHANNEL SEARCH
    */

    const channelSearch =
        document.getElementById("channelSearch");

    const channelCards =
        document.querySelectorAll(".channel-card");

    const searchEmpty =
        document.getElementById("searchEmpty");


    function filterChannels(value) {

        const query =
            value
                .trim()
                .toLowerCase();

        let visibleChannels = 0;


        channelCards.forEach((card) => {

            const channelName =
                card.dataset.channelName || "";

            const channelId =
                card.dataset.channelId || "";


            const matches =
                channelName.includes(query) ||
                channelId.includes(query);


            if (matches) {

                card.style.display = "";

                visibleChannels += 1;

            } else {

                card.style.display = "none";

            }
        });


        if (searchEmpty) {

            searchEmpty.style.display =
                visibleChannels === 0 &&
                channelCards.length > 0
                    ? "flex"
                    : "none";
        }
    }


    if (channelSearch) {

        channelSearch.addEventListener(
            "input",
            (event) => {

                filterChannels(
                    event.target.value
                );
            }
        );
    }


    if (globalSearch) {

        globalSearch.addEventListener(
            "input",
            (event) => {

                const value =
                    event.target.value;

                if (channelSearch) {

                    channelSearch.value =
                        value;
                }

                filterChannels(value);
            }
        );
    }


    /*
        NUMBER COUNTER ANIMATION
    */

    const counters =
        document.querySelectorAll(".counter");


    function formatNumber(number) {

        if (number >= 1000000000) {

            return (
                (number / 1000000000)
                    .toFixed(1)
                    .replace(".0", "")
                + "B"
            );
        }


        if (number >= 1000000) {

            return (
                (number / 1000000)
                    .toFixed(1)
                    .replace(".0", "")
                + "M"
            );
        }


        if (number >= 1000) {

            return (
                (number / 1000)
                    .toFixed(1)
                    .replace(".0", "")
                + "K"
            );
        }


        return number.toLocaleString();
    }


    counters.forEach((counter) => {

        const target =
            Number(
                counter.dataset.value || 0
            );

        const duration = 900;

        const startTime =
            performance.now();


        function animateCounter(currentTime) {

            const progress =
                Math.min(
                    (
                        currentTime -
                        startTime
                    ) / duration,
                    1
                );


            const easedProgress =
                1 -
                Math.pow(
                    1 - progress,
                    3
                );


            const currentValue =
                Math.floor(
                    target *
                    easedProgress
                );


            counter.textContent =
                formatNumber(
                    currentValue
                );


            if (progress < 1) {

                requestAnimationFrame(
                    animateCounter
                );

            } else {

                counter.textContent =
                    formatNumber(target);
            }
        }


        requestAnimationFrame(
            animateCounter
        );
    });


    /*
        CARD MOUSE GLOW
    */

    const cards =
        document.querySelectorAll(
            ".channel-card, .stat-card"
        );


    cards.forEach((card) => {

        card.addEventListener(
            "mousemove",
            (event) => {

                const rect =
                    card.getBoundingClientRect();

                const x =
                    event.clientX -
                    rect.left;

                const y =
                    event.clientY -
                    rect.top;


                card.style.backgroundImage =
                    `
                    radial-gradient(
                        circle at ${x}px ${y}px,
                        rgba(255,255,255,0.075),
                        transparent 120px
                    ),
                    linear-gradient(
                        155deg,
                        rgba(18,23,33,0.96),
                        rgba(10,13,19,0.96)
                    )
                    `;
            }
        );


        card.addEventListener(
            "mouseleave",
            () => {

                card.style.backgroundImage =
                    "";
            }
        );
    });


    /*
        FLASH MESSAGE AUTO HIDE
    */

    const flashMessages =
        document.querySelectorAll(
            ".flash-message"
        );


    flashMessages.forEach(
        (message) => {

            setTimeout(() => {

                message.style.transition =
                    "0.4s ease";

                message.style.opacity =
                    "0";

                message.style.transform =
                    "translateY(-8px)";

                setTimeout(() => {
                    message.remove();
                }, 400);

            }, 4500);
        }
    );

});


/*
    CHANNEL DASHBOARD
    ANIMATED ANALYTICS CHART
*/

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const chart =
            document.getElementById(
                "animatedChart"
            );

        if (!chart) {
            return;
        }


        let values = [];

        try {

            values = JSON.parse(
                chart.dataset.values || "[]"
            );

        } catch (error) {

            console.error(
                "Chart ma'lumotlari xato:",
                error
            );

            return;
        }


        if (!values.length) {
            return;
        }


        const chartLine =
            document.getElementById(
                "chartLine"
            );

        const chartArea =
            document.getElementById(
                "chartArea"
            );

        const chartPoints =
            document.getElementById(
                "chartPoints"
            );


        if (
            !chartLine ||
            !chartArea ||
            !chartPoints
        ) {
            return;
        }


        const width = 700;
        const height = 220;

        const paddingX = 25;
        const paddingY = 25;


        const maxValue =
            Math.max(
                ...values,
                1
            );


        const usableWidth =
            width -
            paddingX * 2;

        const usableHeight =
            height -
            paddingY * 2;


        const points =
            values.map(
                (value, index) => {

                    let x;

                    if (
                        values.length === 1
                    ) {

                        x = width / 2;

                    } else {

                        x =
                            paddingX +
                            (
                                index /
                                (
                                    values.length -
                                    1
                                )
                            ) *
                            usableWidth;
                    }


                    const normalized =
                        Number(value) /
                        maxValue;


                    const y =
                        height -
                        paddingY -
                        normalized *
                        usableHeight;


                    return {
                        x,
                        y,
                        value
                    };
                }
            );


        let linePath = "";


        points.forEach(
            (point, index) => {

                if (index === 0) {

                    linePath +=
                        `M ${point.x} ${point.y}`;

                } else {

                    const previous =
                        points[index - 1];

                    const middleX =
                        (
                            previous.x +
                            point.x
                        ) / 2;


                    linePath +=
                        ` C ${middleX} ${previous.y},` +
                        ` ${middleX} ${point.y},` +
                        ` ${point.x} ${point.y}`;
                }
            }
        );


        const firstPoint =
            points[0];

        const lastPoint =
            points[
                points.length - 1
            ];


        const areaPath =
            linePath +
            ` L ${lastPoint.x} ${height}` +
            ` L ${firstPoint.x} ${height}` +
            " Z";


        chartLine.setAttribute(
            "d",
            linePath
        );


        chartArea.setAttribute(
            "d",
            areaPath
        );


        const totalLength =
            chartLine.getTotalLength();


        chartLine.style.strokeDasharray =
            totalLength;

        chartLine.style.strokeDashoffset =
            totalLength;


        chartLine.style.transition =
            "stroke-dashoffset " +
            "1.4s " +
            "cubic-bezier(.2,.8,.2,1)";


        requestAnimationFrame(
            () => {

                requestAnimationFrame(
                    () => {

                        chartLine.style
                            .strokeDashoffset =
                            "0";
                    }
                );
            }
        );


        points.forEach(
            (point, index) => {

                const dot =
                    document.createElement(
                        "div"
                    );

                dot.className =
                    "chart-dot";


                dot.style.left =
                    (
                        point.x /
                        width *
                        100
                    ) + "%";


                dot.style.top =
                    (
                        point.y /
                        height *
                        100
                    ) + "%";


                dot.style.animationDelay =
                    (
                        0.35 +
                        index * 0.12
                    ) + "s";


                dot.title =
                    Number(
                        point.value
                    ).toLocaleString() +
                    " ko‘rish";


                chartPoints.appendChild(
                    dot
                );
            }
        );
    }
);


/*
    ==========================================
    AI CHANNEL ANALYSIS
    ==========================================
*/

document.addEventListener("DOMContentLoaded", () => {

    const button =
        document.getElementById("aiAnalysisButton");

    const modal =
        document.getElementById("aiAnalysisModal");

    const loading =
        document.getElementById("aiAnalysisLoading");

    const result =
        document.getElementById("aiAnalysisResult");

    const errorBox =
        document.getElementById("aiAnalysisError");

    const againButton =
        document.getElementById("aiAnalyzeAgain");


    if (!button || !modal) {
        return;
    }


    let isLoading = false;


    function openModal() {

        modal.classList.add("open");

        modal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "ai-modal-open"
        );
    }


    function closeModal() {

        if (isLoading) {
            return;
        }

        modal.classList.remove("open");

        modal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "ai-modal-open"
        );
    }


    function setLoading() {

        if (loading) {
            loading.hidden = false;
        }

        if (result) {
            result.hidden = true;
            result.textContent = "";
        }

        if (errorBox) {
            errorBox.hidden = true;
            errorBox.textContent = "";
        }

        if (againButton) {
            againButton.hidden = true;
        }
    }


    async function runAnalysis() {

        if (isLoading) {
            return;
        }


        const endpoint =
            button.dataset.analysisUrl ||
            button.dataset.endpoint;


        openModal();


        if (!endpoint) {

            if (loading) {
                loading.hidden = true;
            }

            if (errorBox) {
                errorBox.textContent =
                    "AI tahlil manzili topilmadi.";

                errorBox.hidden = false;
            }

            return;
        }


        isLoading = true;
        button.disabled = true;

        setLoading();


        try {

            const response =
                await fetch(
                    endpoint,
                    {
                        method: "POST",

                        headers: {
                            "Accept":
                                "application/json",

                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({})
                    }
                );


            let data;


            try {

                data =
                    await response.json();

            } catch (error) {

                throw new Error(
                    "Server noto‘g‘ri javob qaytardi."
                );
            }


            if (
                !response.ok ||
                data.ok === false
            ) {

                throw new Error(
                    data.error ||
                    data.message ||
                    "AI tahlilida xatolik yuz berdi."
                );
            }


            const answer =
                data.analysis ||
                data.result ||
                data.response ||
                data.content;


            if (!answer) {

                throw new Error(
                    "AI javobi bo‘sh qaytdi."
                );
            }


            if (loading) {
                loading.hidden = true;
            }


            if (result) {

                result.textContent =
                    answer;

                result.hidden = false;
            }


            if (againButton) {
                againButton.hidden = false;
            }


        } catch (error) {

            if (loading) {
                loading.hidden = true;
            }


            if (errorBox) {

                errorBox.textContent =
                    error.message ||
                    "AI bilan ulanishda xatolik yuz berdi.";

                errorBox.hidden = false;
            }


            if (againButton) {
                againButton.hidden = false;
            }


            console.error(
                "AI analysis error:",
                error
            );


        } finally {

            isLoading = false;
            button.disabled = false;
        }
    }


    button.addEventListener(
        "click",
        runAnalysis
    );


    if (againButton) {

        againButton.addEventListener(
            "click",
            runAnalysis
        );
    }


    modal
        .querySelectorAll(
            "[data-ai-close]"
        )
        .forEach((item) => {

            item.addEventListener(
                "click",
                closeModal
            );
        });


    document.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Escape" &&
                modal.classList.contains("open")
            ) {

                closeModal();
            }
        }
    );
});


/*
    ==========================================
    AI VIDEO HELPER
    ==========================================
*/

document.addEventListener("DOMContentLoaded", () => {

    const openButton =
        document.getElementById(
            "videoHelperButton"
        );

    const modal =
        document.getElementById(
            "videoHelperModal"
        );

    const topic =
        document.getElementById(
            "videoTopic"
        );

    const generateButton =
        document.getElementById(
            "generateVideoPack"
        );

    const form =
        document.getElementById(
            "videoHelperForm"
        );

    const loading =
        document.getElementById(
            "videoHelperLoading"
        );

    const result =
        document.getElementById(
            "videoHelperResult"
        );

    const errorBox =
        document.getElementById(
            "videoHelperError"
        );

    const againButton =
        document.getElementById(
            "videoHelperAgain"
        );


    if (!openButton || !modal) {
        return;
    }


    let isGenerating = false;


    function openModal() {

        modal.classList.add("open");

        modal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "video-helper-open"
        );


        setTimeout(() => {

            if (topic) {
                topic.focus();
            }

        }, 150);
    }


    function closeModal() {

        if (isGenerating) {
            return;
        }


        modal.classList.remove("open");

        modal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "video-helper-open"
        );
    }


    function showForm() {

        if (form) {
            form.hidden = false;
        }


        if (loading) {
            loading.hidden = true;
        }


        if (result) {

            result.hidden = true;
            result.textContent = "";
        }


        if (errorBox) {

            errorBox.hidden = true;
            errorBox.textContent = "";
        }


        if (againButton) {
            againButton.hidden = true;
        }
    }


    async function generate() {

        if (isGenerating) {
            return;
        }


        const value =
            topic
                ? topic.value.trim()
                : "";


        if (value.length < 3) {

            if (errorBox) {

                errorBox.textContent =
                    "Video mavzusini yozing.";

                errorBox.hidden = false;
            }


            if (topic) {
                topic.focus();
            }

            return;
        }


        const endpoint =
            openButton.dataset.videoHelperUrl ||
            openButton.dataset.endpoint;


        if (!endpoint) {

            if (errorBox) {

                errorBox.textContent =
                    "AI Video Yordamchi manzili topilmadi.";

                errorBox.hidden = false;
            }

            return;
        }


        isGenerating = true;


        if (generateButton) {
            generateButton.disabled = true;
        }


        if (form) {
            form.hidden = true;
        }


        if (result) {
            result.hidden = true;
        }


        if (errorBox) {
            errorBox.hidden = true;
        }


        if (againButton) {
            againButton.hidden = true;
        }


        if (loading) {
            loading.hidden = false;
        }


        try {

            const response =
                await fetch(
                    endpoint,
                    {
                        method: "POST",

                        headers: {

                            "Accept":
                                "application/json",

                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                topic: value
                            })
                    }
                );


            let data;


            try {

                data =
                    await response.json();

            } catch (error) {

                throw new Error(
                    "Serverdan noto‘g‘ri javob qaytdi."
                );
            }


            if (
                !response.ok ||
                data.ok === false
            ) {

                throw new Error(
                    data.error ||
                    data.message ||
                    "AI Video Yordamchida xatolik yuz berdi."
                );
            }


            const answer =
                data.content ||
                data.result ||
                data.analysis ||
                data.response;


            if (!answer) {

                throw new Error(
                    "AI javobi bo‘sh qaytdi."
                );
            }


            if (loading) {
                loading.hidden = true;
            }


            if (result) {

                result.textContent =
                    answer;

                result.hidden = false;
            }


            if (againButton) {
                againButton.hidden = false;
            }


        } catch (error) {

            if (loading) {
                loading.hidden = true;
            }


            if (errorBox) {

                errorBox.textContent =
                    error.message ||
                    "AI bilan ulanishda xatolik yuz berdi.";

                errorBox.hidden = false;
            }


            if (againButton) {
                againButton.hidden = false;
            }


            console.error(
                "AI Video Helper error:",
                error
            );


        } finally {

            isGenerating = false;


            if (generateButton) {
                generateButton.disabled = false;
            }
        }
    }


    openButton.addEventListener(
        "click",
        () => {

            showForm();
            openModal();
        }
    );


    if (generateButton) {

        generateButton.addEventListener(
            "click",
            generate
        );
    }


    if (topic) {

        topic.addEventListener(
            "keydown",
            (event) => {

                if (
                    (
                        event.ctrlKey ||
                        event.metaKey
                    ) &&
                    event.key === "Enter"
                ) {

                    generate();
                }
            }
        );
    }


    if (againButton) {

        againButton.addEventListener(
            "click",
            () => {

                showForm();

                if (topic) {
                    topic.focus();
                }
            }
        );
    }


    modal
        .querySelectorAll(
            "[data-video-helper-close]"
        )
        .forEach((item) => {

            item.addEventListener(
                "click",
                closeModal
            );
        });


    document.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Escape" &&
                modal.classList.contains(
                    "open"
                )
            ) {

                closeModal();
            }
        }
    );
});