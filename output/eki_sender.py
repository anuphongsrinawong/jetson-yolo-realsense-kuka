from __future__ import annotations

from typing import Any, Dict
import xml.etree.ElementTree as ET

from .tcp_sender import TcpSender


class EkiXmlSender:
    """Builds a minimal XML payload suitable for KUKA EKI reception and sends over TCP.

    Note: The exact XML schema must match your EKI XML config on the KUKA controller.
    Adjust tag names or structure via the constructor parameters or by editing build_xml().
    """

    def __init__(
        self,
        host: str,
        port: int,
        logger=None,
        root_tag: str = "EKI",
        only_first_detection: bool = True,
        use_robot_xyz: bool = True,
        pretty: bool = False,
    ) -> None:
        self.tcp = TcpSender(host, port, logger=logger, send_newline=False)
        self.logger = logger
        self.root_tag = root_tag
        self.only_first_detection = only_first_detection
        self.use_robot_xyz = use_robot_xyz
        self.pretty = pretty

    def _build_xml(self, payload: Dict[str, Any]) -> str:
        root = ET.Element(self.root_tag)
        ts = ET.SubElement(root, "TS")
        ts.text = f"{payload.get('ts', 0.0):.6f}"

        frame = payload.get("frame", {})
        ET.SubElement(root, "FrameW").text = str(frame.get("w", 0))
        ET.SubElement(root, "FrameH").text = str(frame.get("h", 0))

        detections = payload.get("detections", [])
        ET.SubElement(root, "NumDet").text = str(len(detections))

        if self.only_first_detection and detections:
            detections = [detections[0]]

        dets_el = ET.SubElement(root, "Detections")
        for i, det in enumerate(detections):
            d_el = ET.SubElement(dets_el, f"Det{i}")
            ET.SubElement(d_el, "Cls").text = str(det.get("class_id", -1))
            ET.SubElement(d_el, "Score").text = f"{det.get('score', 0.0):.4f}"
            bbox = det.get("bbox", [0, 0, 0, 0])
            ET.SubElement(d_el, "X1").text = str(bbox[0])
            ET.SubElement(d_el, "Y1").text = str(bbox[1])
            ET.SubElement(d_el, "X2").text = str(bbox[2])
            ET.SubElement(d_el, "Y2").text = str(bbox[3])

            xyz_key = "xyz_robot" if self.use_robot_xyz and det.get("xyz_robot") is not None else "xyz"
            xyz = det.get(xyz_key)
            if xyz is not None:
                ET.SubElement(d_el, "X").text = f"{xyz[0]:.6f}"
                ET.SubElement(d_el, "Y").text = f"{xyz[1]:.6f}"
                ET.SubElement(d_el, "Z").text = f"{xyz[2]:.6f}"
            else:
                ET.SubElement(d_el, "X").text = "NaN"
                ET.SubElement(d_el, "Y").text = "NaN"
                ET.SubElement(d_el, "Z").text = "NaN"

        xml_bytes = ET.tostring(root, encoding="utf-8")
        xml_str = xml_bytes.decode("utf-8")
        if self.pretty:
            try:
                import xml.dom.minidom as minidom
                xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
            except Exception:
                pass
        return xml_str

    def send(self, payload: Dict[str, Any]) -> None:
        xml_str = self._build_xml(payload)
        self.tcp.send(xml_str)
        if self.logger:
            self.logger.debug(f"EKI XML sent: {len(xml_str)} chars")


