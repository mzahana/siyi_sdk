#include <gst/gst.h>
#include <gst/app/gstappsink.h>
#include <iostream>
#include <opencv2/opencv.hpp>

static gboolean bus_call(GstBus* bus, GstMessage* msg, gpointer data) {
    GMainLoop* loop = (GMainLoop*)data;

    switch (GST_MESSAGE_TYPE(msg)) {

        case GST_MESSAGE_EOS:
            g_main_loop_quit(loop);
            break;

        case GST_MESSAGE_ERROR: {
            gchar* debug;
            GError* error;

            gst_message_parse_error(msg, &error, &debug);
            g_free(debug);

            std::cerr << "Error: " << error->message << std::endl;
            g_error_free(error);

            g_main_loop_quit(loop);
            break;
        }
        default:
            break;
    }

    return TRUE;
}

int main(int argc, char* argv[]) {
    gst_init(&argc, &argv);

    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <RTSP URL>" << std::endl;
        return -1;
    }

    std::string rtsp_url = argv[1];

    GMainLoop* loop = g_main_loop_new(NULL, FALSE);

    // Create GStreamer pipeline
    GstElement* pipeline = gst_pipeline_new("rtsp-pipeline");
    GstElement* src = gst_element_factory_make("rtspsrc", "source");
    GstElement* depay = gst_element_factory_make("rtph264depay", "depay");
    GstElement* h264parse = gst_element_factory_make("h264parse", "h264parse");
    GstElement* decoder = gst_element_factory_make("avdec_h264", "decoder");
    GstElement* videoconvert = gst_element_factory_make("videoconvert", "videoconvert");
    GstElement* appsink = gst_element_factory_make("appsink", "appsink");

    if (!pipeline || !src || !depay || !h264parse || !decoder || !videoconvert || !appsink) {
        std::cerr << "Failed to create GStreamer elements." << std::endl;
        return -1;
    }

    // Set RTSP source properties
    g_object_set(G_OBJECT(src), "location", rtsp_url.c_str(), NULL);
    g_object_set(G_OBJECT(src), "latency", 0, NULL);
    g_object_set(G_OBJECT(src), "udp-reconnect", 1, NULL);

    // Configure appsink
    g_object_set(G_OBJECT(appsink), "emit-signals", TRUE, "sync", FALSE, NULL);
    GstCaps* caps = gst_caps_from_string("video/x-raw, format=(string)BGR");
    gst_app_sink_set_caps(GST_APP_SINK(appsink), caps);
    gst_caps_unref(caps);

    // Add elements to the pipeline
    gst_bin_add_many(GST_BIN(pipeline), src, depay, h264parse, decoder, videoconvert, appsink, NULL);

    // Link elements together
    if (!gst_element_link_many(depay, h264parse, decoder, videoconvert, appsink, NULL)) {
        std::cerr << "Failed to link elements." << std::endl;
        gst_object_unref(pipeline);
        return -1;
    }

    // Connect the pad-added signal
    g_signal_connect(src, "pad-added", G_CALLBACK(+[](GstElement* src, GstPad* new_pad, GstElement* depay) {
        GstPad* sink_pad = gst_element_get_static_pad(depay, "sink");
        if (!gst_pad_is_linked(sink_pad)) {
            gst_pad_link(new_pad, sink_pad);
        }
        gst_object_unref(sink_pad);
    }), depay);

    // Set up bus to handle messages
    GstBus* bus = gst_pipeline_get_bus(GST_PIPELINE(pipeline));
    gst_bus_add_watch(bus, bus_call, loop);

    // Start the pipeline
    gst_element_set_state(pipeline, GST_STATE_PLAYING);

    // Main loop to read frames from appsink
    gboolean quit = FALSE;

    while (!quit) {
        GstSample* sample = gst_app_sink_try_pull_sample(GST_APP_SINK(appsink), GST_SECOND / 10);
        if (sample) {
            GstBuffer* buffer = gst_sample_get_buffer(sample);
            GstCaps* caps = gst_sample_get_caps(sample);
            GstStructure* s = gst_caps_get_structure(caps, 0);

            // Get width and height
            int width, height;
            gst_structure_get_int(s, "width", &width);
            gst_structure_get_int(s, "height", &height);

            GstMapInfo map;
            if (gst_buffer_map(buffer, &map, GST_MAP_READ)) {
                // Convert to OpenCV Mat
                cv::Mat frame(cv::Size(width, height), CV_8UC3, (char*)map.data, cv::Mat::AUTO_STEP);

                // Display the frame
                cv::imshow("RTSP Stream", frame);
                if (cv::waitKey(1) == 'q') {
                    quit = TRUE;
                }

                gst_buffer_unmap(buffer, &map);
            }

            gst_sample_unref(sample);
        } else {
            // No sample available, sleep briefly
            g_usleep(10000); // sleep for 10 ms
        }

        // Check for messages on the bus
        while (gst_bus_have_pending(bus)) {
            GstMessage* msg = gst_bus_pop(bus);
            if (msg != NULL) {
                GError* err;
                gchar* debug_info;

                switch (GST_MESSAGE_TYPE(msg)) {
                    case GST_MESSAGE_ERROR:
                        gst_message_parse_error(msg, &err, &debug_info);
                        std::cerr << "Error received from element " << GST_OBJECT_NAME(msg->src)
                                  << ": " << err->message << std::endl;
                        std::cerr << "Debugging information: " << (debug_info ? debug_info : "none") << std::endl;
                        g_clear_error(&err);
                        g_free(debug_info);
                        quit = TRUE;
                        break;
                    case GST_MESSAGE_EOS:
                        std::cout << "End-Of-Stream reached." << std::endl;
                        quit = TRUE;
                        break;
                    default:
                        // For other messages, do nothing
                        break;
                }
                gst_message_unref(msg);
            }
        }
    }

    // Clean up
    gst_element_set_state(pipeline, GST_STATE_NULL);
    gst_object_unref(bus);
    gst_object_unref(pipeline);
    g_main_loop_unref(loop);

    return 0;
}
