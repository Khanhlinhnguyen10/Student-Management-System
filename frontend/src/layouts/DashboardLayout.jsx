
import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import Sidebar from "../components/layout/Sidebar";
import Header from "../components/layout/Header";
import { ROLE_MENUS } from "../config/roleMenus";

function DashboardLayout({
  user,
  onLogout,
}) {
  // Quản lý việc mở/đóng Sidebar trên màn hình nhỏ
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const location = useLocation();

  // Role chỉ được truyền từ Authentication đã xác thực.
  // Không sử dụng role do người dùng tự chọn ở Login.
  const role = user?.role;

  const menuItems = ROLE_MENUS[role] ?? [];

  // Xác định chức năng đang được truy cập
  const currentMenu = menuItems.find((item) => {
    if (location.pathname === item.path) {
      return true;
    }

    // Dashboard gốc không được nhận nhầm trang con.
    const roleHome = `/${role?.toLowerCase()}`;

    return (
      item.path !== roleHome &&
      location.pathname.startsWith(`${item.path}/`)
    );
  });

  const pageTitle = currentMenu?.label ?? "Dashboard";

  return (
    <div className="min-h-dvh bg-[#F3F9FF] lg:h-dvh lg:overflow-hidden">

      <div className="flex min-h-dvh lg:h-full">

        {/* LEFT: Sidebar */}
        <Sidebar
          role={role}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          onLogout={onLogout}
        />

        {/* RIGHT: Header + Main Content */}
        <div className="flex min-w-0 flex-1 flex-col">

          <Header
            title={pageTitle}
            subtitle="Academic management system"
            user={user}
            onMenuClick={() => setIsSidebarOpen(true)}
          />

          {/* Nội dung trang con */}
          <main
            id="dashboard-main"
            className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-7 lg:px-8"
          >
            <Outlet />
          </main>

        </div>
      </div>
    </div>
  );
}

export default DashboardLayout;
