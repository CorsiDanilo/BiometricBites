import React from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"
import { ReactSession } from "react-client-session"

import { Homepage, LoginPage, NoPage } from "./pages"
import Layout from "./pages/layout"
import AddFace from "./pages/AddFace/AddFace"
import Admin from "./pages/Admin/Admin"

import "./App.scss"

const App = () => {
	ReactSession.setStoreType("sessionStorage")

	return (
		<div className="App">
			<BrowserRouter basename="/">
				<Routes>
					<Route path="/" element={<Layout />}>
						<Route index element={<Homepage />} />
						<Route path="admin" element={<Admin />} />
						<Route path="add-face" element={<AddFace />} />
						<Route path="login" element={<LoginPage />} />
						<Route path="*" element={<NoPage />} />
					</Route>
				</Routes>
			</BrowserRouter>
		</div>
	)
}

export default App
